Install mantis_sim via pybob:

       mkdir mantis-sim-dev
       cd mantis-sim-dev
       git clone git@git.hb.dfki.de:malter/pybob.git
       cd pybob
       ./pybob.py buildconf path="git@git.hb.dfki.de:mantis/buildconf.git"
       cd ..
       source env.sh
       bob-bootstrap mantis/mantis_sim
       cd mantis/mantis_sim
       mars_app -s Szene.smurfs