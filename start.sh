#!/usr/bin/env bash


echo -e ' [*] Modify timezone to Mexico City...\n';
rm /etc/localtime
ln -s /usr/share/zoneinfo/America/Mexico_City /etc/localtime


echo -e ' [*] Saving current environment vars...\n'
# Used by wa_worker/wa_worker/scheduler/taskstore.sh (triggered by crond)
echo '#!/usr/bin/bash' > /tmp/set_environment_vars.sh
chmod 0755 /tmp/set_environment_vars.sh
env > /tmp/environment_vars
sed -e 's/^/export\ /' /tmp/environment_vars >> /tmp/set_environment_vars.sh
rm /tmp/environment_vars


echo -e ' [*] Configuring and starting rsyslogd...\n'
cat /etc/rsyslog.conf | sed 's/\$ModLoad\ imjournal/\#$ModLoad\ imjournal/g' | sed 's/\$OmitLocalLogging on/\$OmitLocalLogging\ off/g' | sed 's/\$IMJournalStateFile/\#\$IMJournalStateFile/g' > /tmp/rsyslog.conf
echo '*.* @@'$SYSLOG_REMOTE >> /tmp/rsyslog.conf
mv /tmp/rsyslog.conf /etc/rsyslog.conf
cat /etc/rsyslog.d/listen.conf | sed 's/\$SystemLogSocketName/\#\$SystemLogSocketName/g' > /tmp/listen.conf
mv /tmp/listen.conf /etc/rsyslog.d/listen.conf
rsyslogd


echo -e ' [*] Starting crond...\n'
crond -p


echo -e ' [*] Loading requirements...\n';
pip install --upgrade pip
yum install -y libjpeg-devel && yum clean all
pip install -r $MOUNT_POINT/wa_worker/requirements.txt
#pip install mysql-connector-python --allow-unverified --allow-external mysql-connector-python
pip install mysql-connector-repackaged


echo -e ' [*] Starting message receiver...\n';
python $MOUNT_POINT/wa_worker/wa_worker/message_receiver/start.py &


echo -e ' [*] Starting scheduler...\n';
python $MOUNT_POINT/wa_worker/wa_worker/scheduler/start.py &


echo -e ' [*] Adding default task...\n'
$MOUNT_POINT/wa_worker/wa_worker/scheduler/utilities/add_venta.sh
$MOUNT_POINT/wa_worker/wa_worker/scheduler/utilities/add_cierre.sh
$MOUNT_POINT/wa_worker/wa_worker/scheduler/utilities/add_flujo_efectivo.sh


while true; do
    echo '.';
    sleep 10;
done
