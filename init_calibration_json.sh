FOLLOWER_ARM_DEST=~/.cache/huggingface/lerobot/calibration/robots/so101_follower/lescholars_follower_arm.json
LEADER_ARM_DEST=~/.cache/huggingface/lerobot/calibration/teleoperators/so101_leader/lescholars_leader_arm.json

cp ./calibration_jsons/lescholars_follower_arm.json $FOLLOWER_ARM_DEST
cp ./calibration_jsons/lescholars_leader_arm.json $LEADER_ARM_DEST