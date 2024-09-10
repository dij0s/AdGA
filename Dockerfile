FROM debian:stable
WORKDIR /usr/bin
RUN apt-get update -y \
  && apt-get install --no-install-recommends -y xvfb libgl1-mesa-dri \
  && rm -rf /var/lib/apt/lists/*
COPY xvfb-startup.sh .
RUN sed -i 's/\r$//' xvfb-startup.sh
ARG RESOLUTION="1920x1080x24"
ENV XVFB_RES="${RESOLUTION}"
ARG XARGS=""
ENV XVFB_ARGS="${XARGS}"
ENTRYPOINT ["/bin/bash", "xvfb-startup.sh"]

RUN apt-get update -y \
  && apt-get install --no-install-recommends -y mesa-utils \
  && rm -rf /var/lib/apt/lists/*
# CMD glxgears

# Rally part.
WORKDIR /app
RUN apt-get update && apt-get install -y git && apt-get clean
RUN git clone https://gitlab.hevs.ch/louis.lettry/rallyrobopilot.git .
RUN git checkout cedric

RUN set -xe \
    && apt-get update \
    && apt-get install -y python3-pip  \
    && apt-get install -y python3-venv

# Set env path. 
ENV VIRTUAL_ENV=/opt/venv
RUN python3 -m venv $VIRTUAL_ENV
ENV PATH="$VIRTUAL_ENV/bin:$PATH"
RUN pip install --upgrade pip && pip install --no-cache-dir -r requirements.txt
RUN pip install python3_xlib

# Make port 8080 available to the world outside this container
EXPOSE 8080

# Define authorizations.
RUN groupadd -g 1000 cedric
RUN useradd -d /home/cedric -s /bin/bash -m cedric -u 1000 -g 1000
USER cedric
ENV HOME=/home/cedric

# Define display variable
ENV DISPLAY=:0

# Run the main.py when the container launches
CMD ["python", "main.py"]
