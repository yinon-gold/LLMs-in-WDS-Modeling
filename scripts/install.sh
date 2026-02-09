# assume that starts from the root of the repository

cd ..

mkdir -p LLMs-in-WDS-Modeling/data
mkdir -p LLMs-in-WDS-Modeling/results

# cloning and copying EPyT documentation

git clone git@github.com:OpenWaterAnalytics/EPyT.git  # ssh
# git clone https://github.com/OpenWaterAnalytics/EPyT.git  # https
cp EPyT/epyt/epanet.py LLMs-in-WDS-Modeling/data/epyt_documentation.py
rm -rf EPyT


# installing dependencies and setting up the environment
cd LLMs-in-WDS-Modeling
uv sync
source .venv/bin/activate
