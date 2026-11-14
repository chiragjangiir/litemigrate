#compdef litemigrate

_litemigrate() {
    local -a commands
    commands=(
        'inspect:Inspect database schema, journal mode, and integrity'
        'validate:Test migration against an isolated shadow copy'
        'apply:Validate on shadow and promote migration safely'
        'report:Render structured audit reports'
    )

    _arguments -C         '--version[Show version information]'         '--help[Show help message]'         '1: :->command'         '*:: :->args'

    case $state in
        command)
            _describe 'commands' commands
            ;;
        args)
            case $line[1] in
                inspect)
                    _arguments                         '--db[Path to SQLite database]:file:_files'                         '--json[Output result in JSON format]'
                    ;;
                validate)
                    _arguments                         '--db[Path to source SQLite database]:file:_files'                         '--migration[Path to SQL migration file]:file:_files'                         '--policy[Path to policy JSON]:file:_files'                         '--strategy[Clone strategy]:(auto apfs_clonefile copy file_backup in_memory)'                         '--output[Output file path]:file:_files'                         '--json[Output in JSON format]'                         '--summary[Output condensed summary]'
                    ;;
                apply)
                    _arguments                         '--db[Path to source SQLite database]:file:_files'                         '--migration[Path to SQL migration file]:file:_files'                         '--policy[Path to policy JSON]:file:_files'                         '--strategy[Clone strategy]:(auto apfs_clonefile copy file_backup in_memory)'                         '--confirm[Explicitly confirm destructive promotion]'                         '--timeout[Lock acquisition timeout in seconds]'                         '--backup-dir[Directory for pre-promotion backups]:directory:_files -/'
                    ;;
                report)
                    _arguments                         '--input[Path to JSON audit report]:file:_files'                         '--json[Normalized JSON output]'
                    ;;
            esac
            ;;
    esac
}

_litemigrate "$@"
