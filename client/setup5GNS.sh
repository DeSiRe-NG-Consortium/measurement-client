sudo ip netns add 5gns
sudo ip link set dev eth1 netns 5gns
sudo ip netns exec 5gns ip link set lo up
sudo ip netns exec 5gns ip link set eth1 up
sudo ip netns exec 5gns udhcpc -i eth1
