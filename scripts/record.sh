# Script/documentation for how to record an asciinema session in the project's venv
# ---------------------------------------------------------------------------------

asciinema rec -c '/bin/bash --rcfile "$(hatch env find)/bin/activate"'

# Then run agg (https://github.com/asciinema/agg) if you need to create a gif
# agg <filename>.cast <filename>.gif --idle-time-limit 10 --last-frame-duration 10
