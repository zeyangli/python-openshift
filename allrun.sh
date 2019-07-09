#停止firewalld服务
systemctl stop firewalld && systemctl disable firewalld

#关闭selinux
sed -i 's/^SELINUX=enforcing$/SELINUX=disabled/' /etc/selinux/config && setenforce 0

#关闭swap设置
swapoff -a
yes | cp /etc/fstab /etc/fstab_bak
cat /etc/fstab_bak |grep -v swap > /etc/fstab

#解决流量路由不正确问题
cat <<EOF >  /etc/sysctl.d/k8s.conf
vm.swappiness = 0
net.bridge.bridge-nf-call-ip6tables = 1
net.bridge.bridge-nf-call-iptables = 1
net.ipv4.ip_forward = 1
EOF

# 使配置生效
modprobe br_netfilter
sysctl -p /etc/sysctl.d/k8s.conf

#更改hosts文件
cat >> /etc/hosts << EOF
192.168.0.20 master.example.com
192.168.0.49 node1.example.com 
192.168.0.50 node2.example.com
EOF

#安装docker
yum -y install docker 
systemctl enable docker && systemctl start docker

#配置阿里k8s源
cat >> /etc/yum.repos.d/k8s.repo << EOF
[kubernetes]
name=kuberbetes repo
baseurl=https://mirrors.aliyun.com/kubernetes/yum/repos/kubernetes-el7-x86_64/
gpgcheck=0
EOF

#安装kubelet/kubeadm/kubectl
yum -y install kubelet kubeadm kubectl
systemctl enable kubelet && systemctl start kubelet

