#_author: hasee
#date: 2019/10/7
import getpass,os
from django.contrib.auth import authenticate
import subprocess
import hashlib,time

class UserPortal(object):
    """用户命令行端交互入口"""

    def __init__(self):
        self.user = None

    def user_auth(self):
        """完成用户交互"""
        retry_count = 0
        while retry_count < 3:
            username = input("Username:").strip()
            if len(username) == 0:continue
            password = getpass.getpass("Password:").strip()
            if len(password)== 0:
                print("Password cannot be null.")
                continue
            user  = authenticate(username= username, password = password)
            if user:
                self.user = user
                #print("welcome login...")
                return
            else:
                print("Invalid username or password!")
            retry_count += 1
        else:
            exit("Too many attempts.")

    def interactive(self):
        """交互函数"""

        self.user_auth()
        if self.user:
            exit_flag = False
            while not  exit_flag:
                for index,host_group in enumerate(self.user.host_groups.all()):
                    print("%s. %s[%s]" %(index,host_group.name, host_group.bind_hosts.all().count()))

                print("%s. Ungrouped Hosts[%s]"%(index+1, self.user.bind_hosts.select_related().count()) )

                user_input = input("Choose Group:").strip()
                if len(user_input) == 0:continue
                if user_input.isdigit():
                    user_input = int(user_input)
                    if user_input >= 0 and user_input < self.user.host_groups.all().count() :
                        selected_hostgroup = self.user.host_groups.all()[user_input]
                    elif user_input == self.user.host_groups.all().count() :#选中了未分组的那组主机
                        selected_hostgroup =  self.user #之所以可以这样，是因为self.user里也有一个bind_hosts,跟HostGroup.bind_hosts指向的表一样
                    else:
                        print("invalid host group")
                        continue
                    while True:
                        for index,bind_host in enumerate(selected_hostgroup.bind_hosts.all()):
                            print("%s. %s(%s user:%s)" % (index,
                                                          bind_host.host.hostname,
                                                          bind_host.host.ip_addr,
                                                          bind_host.host_user.username))

                        user_input2 = input("Choose Host:").strip()
                        if len(user_input2) == 0: continue
                        if user_input2.isdigit():
                            user_input2 = int(user_input2)
                            if user_input2 >= 0 and user_input2 < selected_hostgroup.bind_hosts.all().count() :
                                selected_bindhost = selected_hostgroup.bind_hosts.all()[user_input2]
                                print("logging host",selected_bindhost)
                                md5_str = hashlib.md5(str(time.time()).encode()).hexdigest()
                                login_cmd ='sshpass -p {password} /usr/local/openssh8/bin/ssh {user}@{ip_addr}  -o "StrictHostKeyChecking no" -Z {md5_str}'.format(password=selected_bindhost.host_user.password,
                                                                                                                                user=selected_bindhost.host_user.username,
                                                                                                                                ip_addr=selected_bindhost.host.ip_addr,
                                                                                                                                md5_str = md5_str)


                                print(login_cmd)
                                session_tracker_script=settings.SESSION_TRACKER_SCRIPT
                                tracker_obj=subprocess.Popen("%s %s"%(session_tracker_script,md5_str),shell=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
                                models.SessionLog.objects.create(user=self.user,bind_host=selected_bindhost,session_tag=md5_str)
                                ssh_instance = subprocess.run(login_cmd,shell=True)
                                print("------------logout---------")
                                print("out",tracker_obj.stdout.read())
                                print("err",tracker_obj.stderr.read().decode())
                        if user_input2 == "b":
                            break



if __name__ == "__main__":
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "CrazyAss.settings")
    import django
    django.setup()
    from django.conf import settings
    from audit import models


    portal = UserPortal()
    portal.interactive()
