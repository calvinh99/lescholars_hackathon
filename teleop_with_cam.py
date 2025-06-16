from lerobot.common.cameras.opencv.configuration_opencv import OpenCVCameraConfig
from lerobot.common.teleoperators.so101_leader import SO101LeaderConfig, SO101Leader
from lerobot.common.robots.so101_follower import SO101FollowerConfig, SO101Follower
import rerun as rr
import numpy as np
from datasets import load_dataset
import time
import os
import argparse
import json

def parse_args():
    parser = argparse.ArgumentParser(description='Teleoperation Recording Script')

    # Robot configuration
    parser.add_argument('--robot_type', default='so101_follower', help='Robot type')
    parser.add_argument('--robot_port', default='/dev/ttyACM1', help='Robot port')
    parser.add_argument('--robot_id', default='lescholars_follower_arm', help='Robot ID')

    # Teleop configuration
    parser.add_argument('--teleop_type', default='so101_leader', help='Teleop type')
    parser.add_argument('--teleop_port', default='/dev/ttyACM0', help='Teleop port')
    parser.add_argument('--teleop_id', default='lescholars_leader_arm', help='Teleop ID')

    # Display configuration
    parser.add_argument('--display_data', default='true', help='Display data flag')

    # Dataset configuration
    # parser.add_argument('--dataset_repo_id', required=True, help='Dataset repository ID')
    # parser.add_argument('--dataset_num_episodes', type=int, default=2, help='Number of episodes')
    # parser.add_argument('--dataset_single_task', required=True, help='Task description')

    # Camera configuration
    parser.add_argument('--robot_cameras', default='{ "front": {"type": "opencv", "index_or_path": 4, "width": 640, "height": 480, "fps": 30}}',
                       help='Camera configuration in JSON format')

    return parser.parse_args()

def main():
    args = parse_args()

    # Parse camera configuration
    camera_config = json.loads(args.robot_cameras)
    camera_config = {
        "front": OpenCVCameraConfig(
            index_or_path=camera_config["front"]["index_or_path"],
            width=camera_config["front"]["width"],
            height=camera_config["front"]["height"],
            fps=camera_config["front"]["fps"]
        )
    }

    # Initialize Rerun if display is enabled
    if args.display_data.lower() == 'true':
        rr.init("teleop_visualization", spawn=True)

    # Create dataset directory if it doesn't exist
    os.makedirs("recorded_data", exist_ok=True)

    robot_config = SO101FollowerConfig(
        port=args.robot_port,
        id=args.robot_id,
        cameras=camera_config
    )

    teleop_config = SO101LeaderConfig(
        port=args.teleop_port,
        id=args.teleop_id,
    )

    robot = SO101Follower(robot_config)
    teleop_device = SO101Leader(teleop_config)
    robot.connect()
    teleop_device.connect()

    # Initialize episode counter
    episode_count = 0
    episode_data = []

    try:
        while episode_count < 2:  # Default to 2 episodes since dataset args are commented out
            print(f"\nStarting Episode {episode_count + 1}/2")
            print("Press Enter to start recording, Ctrl+C to stop...")
            input()

            episode_start_time = time.time()
            episode_frames = []

            while True:
                observation = robot.get_observation()
                action = teleop_device.get_action()
                robot.send_action(action)

                # Log camera feed if display is enabled
                if args.display_data.lower() == 'true':
                    if "front" in observation and observation["front"] is not None:
                        rr.log("camera/front", rr.Image(observation["front"]))

                    # Log robot state
                    if hasattr(robot, "get_state"):
                        state = robot.get_state()
                        if state is not None:
                            if hasattr(state, "joint_positions"):
                                rr.log("robot/joint_positions", rr.Scalar(state.joint_positions))
                            if hasattr(state, "end_effector_position"):
                                rr.log("robot/end_effector", rr.Point3D(state.end_effector_position))

                # Record frame data
                frame_data = {
                    "timestamp": time.time() - episode_start_time,
                    "observation": observation,
                    "action": action,
                    "state": state if hasattr(robot, "get_state") else None
                }
                episode_frames.append(frame_data)

    except KeyboardInterrupt:
        print("\nStopping recording...")
    finally:
        # Save the recorded episode
        if episode_frames:
            episode_data.append({
                "task": "teleop_recording",  # Default task name since dataset args are commented out
                "frames": episode_frames
            })
            episode_count += 1

            # Save to dataset
            dataset_path = f"recorded_data/episode_{episode_count}.json"
            with open(dataset_path, 'w') as f:
                json.dump(episode_data[-1], f)
            print(f"Saved episode {episode_count} to {dataset_path}")

        robot.disconnect()
        teleop_device.disconnect()

if __name__ == "__main__":
    main()