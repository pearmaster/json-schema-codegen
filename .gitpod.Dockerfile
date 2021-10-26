
FROM gitpod/workspace-full

RUN apt update -y && apt upgrade -y && apt install -y rapidjson-dev libboost1.71-all-dev