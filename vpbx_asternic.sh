#!/bin/bash
set -e

#Download Installer Script Dependencies
yum install python-pip -y
pip install requests

#Download the Installer Script
wget https://raw.githubusercontent.com/VitalPBX/asternic-stats-installer/master/vpbx_asternic_stats.py

#Executing the Py Script
python vpbx_asternic_stats.py
