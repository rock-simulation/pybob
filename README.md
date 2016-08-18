NOTES:
  - pybob is currently not running on Windows, use the mars_install_scripts
    instead.
  - pybob is a preliminary implementation of an project build system compatible
    to autoproj, if you have problem you might consider using autoproj

Install mars via pybob:

       mkdir mars-dev
       cd mars-dev
       git clone git@github.com:rock-simulation/pybob.git
       cd pybob
       ./pybob.py buildconf path="git@github.com:rock-simulation/simulation-buildconf.git"
       cd ..
       source env.sh

       bob-bootstrap

You can start MARS in the terminal via `mars_app`.
Once you open a new terminal you have to `source env.sh` again.