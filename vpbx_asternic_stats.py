#!/usr/bin/python


import requests
import os
import sys
import tarfile
import shutil
from distutils.dir_util import copy_tree
import subprocess

class asternic_installer:
    url = 'http://download.asternic.net/'
    apache_conf_url = 'https://raw.githubusercontent.com/VitalPBX/asternic-stats-installer/master/ccstats.conf'
    latest_pro_version = 'asternic-stats-pro-2.2.4.tgz'
    latest_lite_version = 'asternic-stats-1.5.tgz'
    local_path = '/usr/src/app_sources'
    installation_path = '/usr/share/ccstats'
    parselog_lite_dir = '/usr/local/parseloglite'
    parselog_dir = '/usr/local/parselog'
    cron_file = '/etc/cron.d/ccstats'
    init_script = '/etc/rc.d/init.d/asterniclog'
    service = '/etc/sysconfig/asterniclog'
    apache_conf_local = '/etc/httpd/conf.d/ccstats.conf'

    def __init__(self, version):
        self.version = version.lower()
        tar = self.tar_file = self.latest_pro_version if self.version == 'p' or self.version == 'pro' else self.latest_lite_version
        self.uncompress_dir = self.local_path + "/" + ('.').join(tar.split('.')[:-1]) #Removing the file extension to obtain the folder name
        self.pro_version = True if self.version == 'p' or self.version == 'pro' else False
        if not self.pro_version:
            self.uncompress_dir = self.local_path + "/asternic-stats"

    def run(self):
        self.pre_clean()
        self.build_asternic_dirs()
        self.download()
        self.uncompress()
        self.copy_files()
        self.db_installation()
        self.post_installation()

    def post_installation(self):
        print ("Ending Installation")
        os.system("systemctl restart httpd")
        os.system("systemctl restart crond.service")
        if self.pro_version:
            os.system("/sbin/chkconfig --add asterniclog")
            os.system("systemctl enable asterniclog.service")
            os.system("systemctl restart asterniclog")

        print ("Setting Permissions")
        os.system("chown -R apache:apache " + self.installation_path)
        os.system("chmod +x -R " + self.parselog_dir)
        os.system("chmod +x -R " + self.parselog_lite_dir)

        print ("Setting AMI User and Password")
        manager_user_var = '$MANAGER_USER' if self.pro_version else '$manager_user'
        manager_secret_var = '$MANAGER_SECRET' if self.pro_version else '$manager_secret'
        os.system("sed -i --follow-symlinks 's/^"+manager_user_var+"[ ]*=.*/\\"+manager_user_var+"=\"astmanager\"\;/g' " + self.installation_path + '/config.php')
        os.system("sed -i --follow-symlinks 's/^"+manager_secret_var+"[ ]*=.*/\\"+manager_secret_var+"=\"Xn75CFbVfjRg71v\"\;/g' " + self.installation_path + '/config.php')

        print("\033[92mThe CCStats has been installed successfully\033[0m")
        print("\033[92mTo access to it, you must to go to http://YOUR-IP/ccstats\033[0m")

    def db_installation(self):
        db = 'qstats' if self.pro_version else 'qstatslite'
        main_sql = self.uncompress_dir + '/sql/mysql-tables.sql' if self.pro_version else self.uncompress_dir + '/sql/qstats.sql'

        os.system('mysqladmin -u root create ' + db)
        self.import_sql_file(db,main_sql)
        if self.pro_version:
            self.import_sql_file(db,self.uncompress_dir + '/sql/trigger.sql')
            os.system('mysql -uroot -e"GRANT all privileges on qstats.* to qstatsUser@localhost identified by \'qstatsPassw0rd\'"')

    def import_sql_file(self, db, sql_file):
        process = subprocess.Popen(['mysql', db, '-uroot'],
                        stdout=subprocess.PIPE, stdin=subprocess.PIPE)
        output = process.communicate('source ' + sql_file)[0]

    def copy_files(self):
        print("Copying files...")
        parselog_dir = self.parselog_dir if self.pro_version else self.parselog_lite_dir

        print("Copying files to: " + parselog_dir)
        copy_tree(self.uncompress_dir + "/parselog", parselog_dir)

        print("Copying files to: " + self.installation_path)
        copy_tree(self.uncompress_dir + "/html", self.installation_path)

        if self.pro_version:
            shutil.copy(self.uncompress_dir + "/init/sysconfig.asterniclog", self.service)
            shutil.copy(self.uncompress_dir + "/init/asterniclog.redhat", self.init_script)
        else:
            with open(self.cron_file, 'w') as f:
                f.write('* * * * * root /usr/local/parseloglite/parselog.php convertlocal\n')
                f.close()

        print("Installing Apache Configuration in: " + self.apache_conf_local)
        req = requests.get(self.apache_conf_url)
        if req.status_code == 200:
            with open(self.apache_conf_local, "w") as code:
                code.write(req.content)
        else:
            sys.exit("Cannot Download the following file: " + source_url)

    def build_asternic_dirs(self):
        directories = [self.local_path, self.installation_path, self.installation_path]
        if self.pro_version:
            directories.append(self.parselog_dir)
        else:
            directories.append(self.parselog_lite_dir)

        for d in directories:
            if not os.path.isdir(d):
                os.makedirs(d)

    def uncompress(self):
        tar = tarfile.open(self.filename, "r:gz")
        tar.extractall(self.local_path)
        tar.close()

    def pre_clean(self):
        print("Droping DB if Exists")
        os.system('mysql -uroot -e"drop database if exists qstats"')
        os.system('mysql -uroot -e"drop database if exists qstatslite"')

        directories = [self.uncompress_dir, self.installation_path, self.parselog_dir, self.parselog_lite_dir]
        for d in directories:
            if os.path.isdir(d):
                print("Removing: " + d)
                shutil.rmtree(d)

        files = [self.cron_file, self.service, self.init_script]
        for f in files:
            if os.path.isfile(f):
                print("Removing: " + f)
                os.remove(f)

    def exec_cmd(self, command):
        output = subprocess.Popen(command.split(), stdout = subprocess.PIPE).communicate()[0]
        print output

    def download(self):
        tar = self.tar_file
        source_url = self.url + tar
        print("Downloading: " + source_url)
        req = requests.get(source_url)
        if req.status_code == 200:
            self.filename = self.local_path + "/" + tar
            with open(self.filename, "wb") as code:
                code.write(req.content)
        else:
            sys.exit("Cannot Download the following file: " + source_url)

def check_input(prompt, values_list):
    print "\n"
    while True:
        result = raw_input(prompt).strip()
        if result.lower() in values_list:
            return result

        print("Please enter an appropriate value --> " + ", ".join(values_list))

asternic_version = check_input("\033[92mWould you like to install Asternic Stats PRO or Lite? (P/L)\033[0m",['p', 'pro', 'l', 'lite'])
i = asternic_installer(asternic_version)
i.run()
