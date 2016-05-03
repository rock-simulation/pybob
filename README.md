Install mantis_sim via pybob:

       mkdir mantis-sim-dev
       cd mantis-sim-dev
       git clone git@git.hb.dfki.de:malter/pybob.git
       cd pybob
       ./pybob.py buildconf path="git@git.hb.dfki.de:mantis/buildconf.git"
       cd ..
       source env.sh

Due to the fact that control/urdfdom is broken the following is bit more complex than necessary:

       bob-fetch mantis/mantis_sim

Revert the last merge in control/urdfdom then continue with:

       bob-install mantis/mantis_sim
       cd mantis/mantis_sim
       mars_app -s Szene.smurfs