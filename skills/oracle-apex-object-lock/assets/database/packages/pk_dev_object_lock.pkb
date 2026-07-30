create or replace package body "PK_DEV_OBJECT_LOCK" as

    function func_runtime_version return varchar2 deterministic
    is
    begin
        return c_runtime_version;
    end func_runtime_version;

    function normalizar_tipo (
        p_object_type in varchar2
    ) return varchar2
    is
        l_tipo varchar2(30) := upper(trim(p_object_type));
    begin
        if l_tipo in ('PACKAGE BODY', 'PACKAGE SPEC', 'PACKAGE SPECIFICATION', 'PKB', 'PKS') then
            return 'PACKAGE';
        end if;

        if l_tipo in ('TYPE BODY', 'TYPE SPEC', 'TYPE SPECIFICATION') then
            return 'TYPE';
        end if;

        if l_tipo is null then
            return 'PACKAGE';
        end if;

        return l_tipo;
    end normalizar_tipo;

    function normalizar_nome (
        p_object_name in varchar2
    ) return varchar2
    is
    begin
        return upper(replace(trim(p_object_name), '"'));
    end normalizar_nome;

    function normalizar_flag (
        p_flag in varchar2
    ) return varchar2
    is
    begin
        return case when upper(trim(p_flag)) = 'S' then 'S' else 'N' end;
    end normalizar_flag;

    function ator_atual (
        p_lock_owner in varchar2
    ) return varchar2
    is
        l_owner varchar2(255);
    begin
        l_owner := trim(p_lock_owner);

        if l_owner is null then
            l_owner := sys_context('USERENV', 'CLIENT_IDENTIFIER');
        end if;

        if l_owner is null then
            l_owner := sys_context('USERENV', 'OS_USER');
        end if;

        if l_owner is null then
            l_owner := user;
        end if;

        return substr(l_owner, 1, 255);
    end ator_atual;

    procedure validar_entrada (
          p_object_name in varchar2
        , p_object_type in varchar2
        , p_ttl_minutos in number default 240
    )
    is
        l_tipo varchar2(30) := normalizar_tipo(p_object_type);
        l_nome varchar2(128) := normalizar_nome(p_object_name);
    begin
        if l_nome is null then
            raise_application_error(-20080, 'Nome do objeto obrigatorio para lock de desenvolvimento.');
        end if;

        if l_tipo not in ('PACKAGE', 'VIEW', 'TRIGGER', 'PROCEDURE', 'FUNCTION', 'TYPE', 'SYNONYM') then
            raise_application_error(-20081, 'Tipo de objeto nao suportado para lock de desenvolvimento: ' || l_tipo);
        end if;

        if p_ttl_minutos is not null and (p_ttl_minutos < 15 or p_ttl_minutos > 1440) then
            raise_application_error(-20082, 'TTL do lock deve ficar entre 15 e 1440 minutos.');
        end if;
    end validar_entrada;

    procedure validar_janela_recente (
        p_horas in number
    )
    is
    begin
        if nvl(p_horas, 48) < 1 or nvl(p_horas, 48) > 720 then
            raise_application_error(-20090, 'Janela de lock recente deve ficar entre 1 e 720 horas.');
        end if;
    end validar_janela_recente;

    procedure expirar_locks_vencidos
    is
    begin
        update dev_object_lock
           set lock_status = 'EXPIRED',
               released_at = systimestamp,
               released_by = 'PK_DEV_OBJECT_LOCK',
               release_reason = 'Lock expirado automaticamente por TTL.'
         where lock_status = 'ACTIVE'
           and lock_expires_at < systimestamp;
    end expirar_locks_vencidos;

    procedure proc_expirar_locks
    is
        pragma autonomous_transaction;
    begin
        expirar_locks_vencidos;
        commit;
    exception
        when others then
            rollback;
            raise;
    end proc_expirar_locks;

    procedure proc_adquirir_lock (
          p_object_name  in varchar2
        , p_object_type  in varchar2 default 'PACKAGE'
        , p_lock_owner   in varchar2 default null
        , p_branch_name  in varchar2 default null
        , p_task_ref     in varchar2 default null
        , p_context      in varchar2 default null
        , p_repo_base_ref in varchar2 default null
        , p_repo_head_ref in varchar2 default null
        , p_repo_start_sha in varchar2 default null
        , p_ttl_minutos  in number   default 240
        , p_forcar       in varchar2 default 'N'
    )
    is
        pragma autonomous_transaction;

        l_tipo             varchar2(30)  := normalizar_tipo(p_object_type);
        l_nome             varchar2(128) := normalizar_nome(p_object_name);
        l_ator             varchar2(255) := ator_atual(p_lock_owner);
        l_forcar           varchar2(1)   := normalizar_flag(p_forcar);
        l_lock_id          dev_object_lock.ad_dev_object_lock%type;
        l_locked_by        dev_object_lock.locked_by%type;
        l_branch_name      dev_object_lock.branch_name%type;
        l_task_ref         dev_object_lock.task_ref%type;
        l_lock_expires_at  dev_object_lock.lock_expires_at%type;
    begin
        validar_entrada(l_nome, l_tipo, nvl(p_ttl_minutos, 240));
        expirar_locks_vencidos;

        begin
            select ad_dev_object_lock,
                   locked_by,
                   branch_name,
                   task_ref,
                   lock_expires_at
              into l_lock_id,
                   l_locked_by,
                   l_branch_name,
                   l_task_ref,
                   l_lock_expires_at
              from dev_object_lock
             where object_owner = user
               and object_type = l_tipo
               and object_name = l_nome
               and lock_status = 'ACTIVE'
             for update;
        exception
            when no_data_found then
                l_lock_id := null;
        end;

        if l_lock_id is not null then
            if l_locked_by = l_ator then
                update dev_object_lock
                   set last_heartbeat_at = systimestamp,
                       lock_expires_at = systimestamp + numtodsinterval(nvl(p_ttl_minutos, 240), 'MINUTE'),
                       branch_name = substr(nvl(trim(p_branch_name), branch_name), 1, 255),
                       task_ref = substr(nvl(trim(p_task_ref), task_ref), 1, 500),
                       lock_context = substr(nvl(trim(p_context), lock_context), 1, 4000),
                       repo_base_ref = substr(nvl(trim(p_repo_base_ref), repo_base_ref), 1, 255),
                       repo_head_ref = substr(nvl(trim(p_repo_head_ref), repo_head_ref), 1, 255),
                       repo_start_sha = substr(nvl(trim(p_repo_start_sha), repo_start_sha), 1, 64)
                 where ad_dev_object_lock = l_lock_id;

                dbms_output.put_line('Lock renovado: ' || l_tipo || ' ' || l_nome || ' por ' || l_ator || '.');
            elsif l_forcar = 'S' then
                update dev_object_lock
                   set lock_status = 'RELEASED',
                       released_at = systimestamp,
                       released_by = l_ator,
                       release_reason = 'Substituido por aquisicao forcada.'
                 where ad_dev_object_lock = l_lock_id;

                insert into dev_object_lock (
                    object_owner,
                    object_type,
                    object_name,
                    lock_status,
                    locked_by,
                    branch_name,
                    task_ref,
                    lock_context,
                    repo_base_ref,
                    repo_head_ref,
                    repo_start_sha,
                    locked_at,
                    last_heartbeat_at,
                    lock_expires_at
                ) values (
                    user,
                    l_tipo,
                    l_nome,
                    'ACTIVE',
                    l_ator,
                    substr(trim(p_branch_name), 1, 255),
                    substr(trim(p_task_ref), 1, 500),
                    substr(trim(p_context), 1, 4000),
                    substr(trim(p_repo_base_ref), 1, 255),
                    substr(trim(p_repo_head_ref), 1, 255),
                    substr(trim(p_repo_start_sha), 1, 64),
                    systimestamp,
                    systimestamp,
                    systimestamp + numtodsinterval(nvl(p_ttl_minutos, 240), 'MINUTE')
                );

                dbms_output.put_line('Lock forcado: ' || l_tipo || ' ' || l_nome || ' por ' || l_ator || '.');
            else
                raise_application_error(
                    -20083,
                    'Objeto bloqueado por outro desenvolvedor/agente: ' || l_tipo || ' ' || l_nome ||
                    ' | dono=' || l_locked_by ||
                    ' | branch=' || nvl(l_branch_name, '-') ||
                    ' | tarefa=' || nvl(l_task_ref, '-') ||
                    ' | expira=' || to_char(l_lock_expires_at, 'YYYY-MM-DD HH24:MI:SS TZH:TZM')
                );
            end if;
        else
            insert into dev_object_lock (
                object_owner,
                object_type,
                object_name,
                lock_status,
                locked_by,
                branch_name,
                task_ref,
                lock_context,
                repo_base_ref,
                repo_head_ref,
                repo_start_sha,
                locked_at,
                last_heartbeat_at,
                lock_expires_at
            ) values (
                user,
                l_tipo,
                l_nome,
                'ACTIVE',
                l_ator,
                substr(trim(p_branch_name), 1, 255),
                substr(trim(p_task_ref), 1, 500),
                substr(trim(p_context), 1, 4000),
                substr(trim(p_repo_base_ref), 1, 255),
                substr(trim(p_repo_head_ref), 1, 255),
                substr(trim(p_repo_start_sha), 1, 64),
                systimestamp,
                systimestamp,
                systimestamp + numtodsinterval(nvl(p_ttl_minutos, 240), 'MINUTE')
            );

            dbms_output.put_line('Lock adquirido: ' || l_tipo || ' ' || l_nome || ' por ' || l_ator || '.');
        end if;

        commit;
    exception
        when dup_val_on_index then
            rollback;
            raise_application_error(-20084, 'Nao foi possivel adquirir o lock porque outro agente registrou o mesmo objeto ao mesmo tempo. Consulte VW_DEV_OBJECT_LOCK_ATIVO e tente novamente.');
        when others then
            rollback;
            raise;
    end proc_adquirir_lock;

    procedure proc_renovar_lock (
          p_object_name  in varchar2
        , p_object_type  in varchar2 default 'PACKAGE'
        , p_lock_owner   in varchar2 default null
        , p_ttl_minutos  in number   default 240
        , p_forcar       in varchar2 default 'N'
    )
    is
        pragma autonomous_transaction;

        l_tipo     varchar2(30)  := normalizar_tipo(p_object_type);
        l_nome     varchar2(128) := normalizar_nome(p_object_name);
        l_ator     varchar2(255) := ator_atual(p_lock_owner);
        l_forcar   varchar2(1)   := normalizar_flag(p_forcar);
        l_qtd      number;
    begin
        validar_entrada(l_nome, l_tipo, nvl(p_ttl_minutos, 240));
        expirar_locks_vencidos;

        update dev_object_lock
           set last_heartbeat_at = systimestamp,
               lock_expires_at = systimestamp + numtodsinterval(nvl(p_ttl_minutos, 240), 'MINUTE')
         where object_owner = user
           and object_type = l_tipo
           and object_name = l_nome
           and lock_status = 'ACTIVE'
           and (locked_by = l_ator or l_forcar = 'S');

        l_qtd := sql%rowcount;

        if l_qtd = 0 then
            raise_application_error(-20085, 'Lock ativo nao encontrado para renovacao ou pertence a outro desenvolvedor/agente.');
        end if;

        dbms_output.put_line('Lock renovado: ' || l_tipo || ' ' || l_nome || ' por ' || l_ator || '.');
        commit;
    exception
        when others then
            rollback;
            raise;
    end proc_renovar_lock;

    procedure proc_liberar_lock (
          p_object_name      in varchar2
        , p_object_type      in varchar2 default 'PACKAGE'
        , p_lock_owner       in varchar2 default null
        , p_release_reason   in varchar2 default null
        , p_repo_end_sha     in varchar2 default null
        , p_forcar           in varchar2 default 'N'
    )
    is
        pragma autonomous_transaction;

        l_tipo     varchar2(30)  := normalizar_tipo(p_object_type);
        l_nome     varchar2(128) := normalizar_nome(p_object_name);
        l_ator     varchar2(255) := ator_atual(p_lock_owner);
        l_forcar   varchar2(1)   := normalizar_flag(p_forcar);
        l_qtd      number;
    begin
        validar_entrada(l_nome, l_tipo, null);
        expirar_locks_vencidos;

        update dev_object_lock
           set lock_status = 'RELEASED',
               released_at = systimestamp,
               released_by = l_ator,
               release_reason = substr(nvl(trim(p_release_reason), 'Liberado pelo dono do lock.'), 1, 4000),
               repo_end_sha = substr(nvl(trim(p_repo_end_sha), repo_end_sha), 1, 64)
         where object_owner = user
           and object_type = l_tipo
           and object_name = l_nome
           and lock_status = 'ACTIVE'
           and (locked_by = l_ator or l_forcar = 'S');

        l_qtd := sql%rowcount;

        if l_qtd = 0 then
            raise_application_error(-20086, 'Lock ativo nao encontrado para liberacao ou pertence a outro desenvolvedor/agente.');
        end if;

        dbms_output.put_line('Lock liberado: ' || l_tipo || ' ' || l_nome || ' por ' || l_ator || '.');
        commit;
    exception
        when others then
            rollback;
            raise;
    end proc_liberar_lock;

    procedure proc_assert_lock_compilacao (
          p_object_name  in varchar2
        , p_object_type  in varchar2 default 'PACKAGE'
        , p_lock_owner   in varchar2 default null
    )
    is
        l_tipo             varchar2(30)  := normalizar_tipo(p_object_type);
        l_nome             varchar2(128) := normalizar_nome(p_object_name);
        l_ator             varchar2(255) := ator_atual(p_lock_owner);
        l_locked_by        dev_object_lock.locked_by%type;
        l_branch_name      dev_object_lock.branch_name%type;
        l_task_ref         dev_object_lock.task_ref%type;
        l_lock_expires_at  dev_object_lock.lock_expires_at%type;
    begin
        validar_entrada(l_nome, l_tipo, null);
        proc_expirar_locks;

        begin
            select locked_by,
                   branch_name,
                   task_ref,
                   lock_expires_at
              into l_locked_by,
                   l_branch_name,
                   l_task_ref,
                   l_lock_expires_at
              from dev_object_lock
             where object_owner = user
               and object_type = l_tipo
               and object_name = l_nome
               and lock_status = 'ACTIVE'
               and lock_expires_at >= systimestamp;
        exception
            when no_data_found then
                raise_application_error(-20087, 'Objeto sem lock ativo: ' || l_tipo || ' ' || l_nome || '. Adquira lock antes de compilar no DEV.');
        end;

        if l_locked_by != l_ator then
            raise_application_error(
                -20088,
                'Compilacao bloqueada. Objeto com lock de outro desenvolvedor/agente: ' || l_tipo || ' ' || l_nome ||
                ' | dono=' || l_locked_by ||
                ' | branch=' || nvl(l_branch_name, '-') ||
                ' | tarefa=' || nvl(l_task_ref, '-') ||
                ' | expira=' || to_char(l_lock_expires_at, 'YYYY-MM-DD HH24:MI:SS TZH:TZM')
            );
        end if;

        dbms_output.put_line('Lock confirmado para compilacao: ' || l_tipo || ' ' || l_nome || ' por ' || l_ator || '.');
    end proc_assert_lock_compilacao;

    function func_status_lock (
          p_object_name in varchar2
        , p_object_type in varchar2 default 'PACKAGE'
    ) return varchar2
    is
        l_tipo             varchar2(30)  := normalizar_tipo(p_object_type);
        l_nome             varchar2(128) := normalizar_nome(p_object_name);
        l_locked_by        dev_object_lock.locked_by%type;
        l_branch_name      dev_object_lock.branch_name%type;
        l_task_ref         dev_object_lock.task_ref%type;
        l_lock_expires_at  dev_object_lock.lock_expires_at%type;
    begin
        validar_entrada(l_nome, l_tipo, null);

        select locked_by,
               branch_name,
               task_ref,
               lock_expires_at
          into l_locked_by,
               l_branch_name,
               l_task_ref,
               l_lock_expires_at
          from dev_object_lock
         where object_owner = user
           and object_type = l_tipo
           and object_name = l_nome
           and lock_status = 'ACTIVE'
           and lock_expires_at >= systimestamp;

        return 'LOCK_ATIVO | objeto=' || l_tipo || ' ' || l_nome ||
               ' | dono=' || l_locked_by ||
               ' | branch=' || nvl(l_branch_name, '-') ||
               ' | tarefa=' || nvl(l_task_ref, '-') ||
               ' | expira=' || to_char(l_lock_expires_at, 'YYYY-MM-DD HH24:MI:SS TZH:TZM');
    exception
        when no_data_found then
            return 'SEM_LOCK_ATIVO | objeto=' || l_tipo || ' ' || l_nome;
    end func_status_lock;

    function func_status_recente (
          p_object_name in varchar2
        , p_object_type in varchar2 default 'PACKAGE'
        , p_horas       in number   default 48
    ) return varchar2
    is
        l_tipo            varchar2(30)  := normalizar_tipo(p_object_type);
        l_nome            varchar2(128) := normalizar_nome(p_object_name);
        l_lock_status     dev_object_lock.lock_status%type;
        l_locked_by       dev_object_lock.locked_by%type;
        l_branch_name     dev_object_lock.branch_name%type;
        l_task_ref        dev_object_lock.task_ref%type;
        l_locked_at       dev_object_lock.locked_at%type;
        l_released_at     dev_object_lock.released_at%type;
        l_repo_base_ref   dev_object_lock.repo_base_ref%type;
        l_repo_head_ref   dev_object_lock.repo_head_ref%type;
        l_repo_start_sha  dev_object_lock.repo_start_sha%type;
        l_repo_end_sha    dev_object_lock.repo_end_sha%type;
    begin
        validar_entrada(l_nome, l_tipo, null);
        validar_janela_recente(p_horas);

        select lock_status,
               locked_by,
               branch_name,
               task_ref,
               locked_at,
               released_at,
               repo_base_ref,
               repo_head_ref,
               repo_start_sha,
               repo_end_sha
          into l_lock_status,
               l_locked_by,
               l_branch_name,
               l_task_ref,
               l_locked_at,
               l_released_at,
               l_repo_base_ref,
               l_repo_head_ref,
               l_repo_start_sha,
               l_repo_end_sha
          from (
                select lock_status,
                       locked_by,
                       branch_name,
                       task_ref,
                       locked_at,
                       released_at,
                       repo_base_ref,
                       repo_head_ref,
                       repo_start_sha,
                       repo_end_sha,
                       nvl(released_at, last_heartbeat_at) as dt_referencia
                  from dev_object_lock
                 where object_owner = user
                   and object_type = l_tipo
                   and object_name = l_nome
                   and nvl(released_at, last_heartbeat_at) >= systimestamp - numtodsinterval(nvl(p_horas, 48), 'HOUR')
                 order by nvl(released_at, last_heartbeat_at) desc
               )
         where rownum = 1;

        return 'LOCK_RECENTE | objeto=' || l_tipo || ' ' || l_nome ||
               ' | status=' || l_lock_status ||
               ' | dono=' || l_locked_by ||
               ' | branch=' || nvl(l_branch_name, '-') ||
               ' | tarefa=' || nvl(l_task_ref, '-') ||
               ' | inicio=' || to_char(l_locked_at, 'YYYY-MM-DD HH24:MI:SS TZH:TZM') ||
               ' | liberado=' || nvl(to_char(l_released_at, 'YYYY-MM-DD HH24:MI:SS TZH:TZM'), '-') ||
               ' | base=' || nvl(l_repo_base_ref, '-') ||
               ' | head=' || nvl(l_repo_head_ref, '-') ||
               ' | sha_inicio=' || nvl(l_repo_start_sha, '-') ||
               ' | sha_fim=' || nvl(l_repo_end_sha, '-');
    exception
        when no_data_found then
            return 'SEM_LOCK_RECENTE | objeto=' || l_tipo || ' ' || l_nome || ' | janela_horas=' || to_char(nvl(p_horas, 48));
    end func_status_recente;

end "PK_DEV_OBJECT_LOCK";
/
