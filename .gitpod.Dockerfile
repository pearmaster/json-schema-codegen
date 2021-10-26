
FROM gitpod/workspace-full

RUN sudo apt update -y && sudo apt upgrade -y && sudo apt install -y rapidjson-dev libboost1.71-all-dev
