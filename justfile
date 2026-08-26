list:
    just --list

run arg1="" arg2=""  arg3 = "":
    uv run src/projects/main.py {{arg1}} {{arg2}} {{arg3}}

test arg1="":
    uv run -m pytest {{arg1}}
    
import '/home/jeff/.config/just/dev-packages.just'