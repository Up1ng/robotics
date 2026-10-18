FROM ros:jazzy-ros-base@sha256:103b6c417973394659af6804d4917cd489b91e5ed22eb7bef263025a3bed2410
RUN apt-get update -qq && DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends \
    ros-jazzy-turtlesim ros-jazzy-rosbag2-storage-mcap \
    python3-pytest python3-yaml ros-jazzy-ament-flake8 ros-jazzy-ament-pep257 \
    ros-jazzy-ament-copyright git \
    && rm -rf /var/lib/apt/lists/*
WORKDIR /workspace
ENV QT_QPA_PLATFORM=offscreen
