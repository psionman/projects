list:
    just --list

run arg1="":
    uv run src/projects/main.py {{arg1}}

test arg1="":
    uv run -m pytest {{arg1}}
