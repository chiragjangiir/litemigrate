#!/usr/bin/env bash
# Bash completion script for litemigrate

_litemigrate_completions() {
    local cur prev commands
    cur="${COMP_WORDS[COMP_CWORD]}"
    prev="${COMP_WORDS[COMP_CWORD-1]}"
    commands="inspect validate apply report --help --version"

    case "${prev}" in
        inspect)
            COMPREPLY=( $(compgen -W "--db --json --help" -- "${cur}") )
            return 0
            ;;
        validate)
            COMPREPLY=( $(compgen -W "--db --migration --policy --strategy --output --json --summary --help" -- "${cur}") )
            return 0
            ;;
        apply)
            COMPREPLY=( $(compgen -W "--db --migration --policy --strategy --confirm --timeout --backup-dir --help" -- "${cur}") )
            return 0
            ;;
        report)
            COMPREPLY=( $(compgen -W "--input --json --help" -- "${cur}") )
            return 0
            ;;
        --db|--migration|--policy|--output|--input|--backup-dir)
            COMPREPLY=( $(compgen -f -- "${cur}") )
            return 0
            ;;
        --strategy)
            COMPREPLY=( $(compgen -W "auto apfs_clonefile copy file_backup in_memory" -- "${cur}") )
            return 0
            ;;
    esac

    if [[ ${COMP_CWORD} -eq 1 ]]; then
        COMPREPLY=( $(compgen -W "${commands}" -- "${cur}") )
        return 0
    fi
}

complete -F _litemigrate_completions litemigrate
