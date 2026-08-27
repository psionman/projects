package_name := `basename $(pwd)`
script := "uv run src/" + package_name + "/main.py"
    
import '/home/jeff/.config/just/dev-packages.just'