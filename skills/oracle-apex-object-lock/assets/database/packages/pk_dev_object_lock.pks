create or replace package "PK_DEV_OBJECT_LOCK" as

    c_runtime_version constant varchar2(20) := '1.1.0';

    function func_runtime_version return varchar2 deterministic;

    procedure proc_expirar_locks;

    procedure proc_purgar_historico (
        p_keep_days in number default 30
    );

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
    );

    procedure proc_renovar_lock (
          p_object_name  in varchar2
        , p_object_type  in varchar2 default 'PACKAGE'
        , p_lock_owner   in varchar2 default null
        , p_ttl_minutos  in number   default 240
        , p_forcar       in varchar2 default 'N'
    );

    procedure proc_liberar_lock (
          p_object_name      in varchar2
        , p_object_type      in varchar2 default 'PACKAGE'
        , p_lock_owner       in varchar2 default null
        , p_release_reason   in varchar2 default null
        , p_repo_end_sha     in varchar2 default null
        , p_forcar           in varchar2 default 'N'
    );

    procedure proc_assert_lock_compilacao (
          p_object_name  in varchar2
        , p_object_type  in varchar2 default 'PACKAGE'
        , p_lock_owner   in varchar2 default null
    );

    function func_status_lock (
          p_object_name in varchar2
        , p_object_type in varchar2 default 'PACKAGE'
    ) return varchar2;

    function func_status_recente (
          p_object_name in varchar2
        , p_object_type in varchar2 default 'PACKAGE'
        , p_horas       in number   default 48
    ) return varchar2;

end "PK_DEV_OBJECT_LOCK";
/
