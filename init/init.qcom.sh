#! /vendor/bin/sh

# Copyright (c) 2009-2016, The Linux Foundation. All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#     * Redistributions of source code must retain the above copyright
#       notice, this list of conditions and the following disclaimer.
#     * Redistributions in binary form must reproduce the above copyright
#       notice, this list of conditions and the following disclaimer in the
#       documentation and/or other materials provided with the distribution.
#     * Neither the name of The Linux Foundation nor
#       the names of its contributors may be used to endorse or promote
#       products derived from this software without specific prior written
#       permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
# NON-INFRINGEMENT ARE DISCLAIMED.  IN NO EVENT SHALL THE COPYRIGHT OWNER OR
# CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL,
# EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO,
# PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS;
# OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY,
# WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR
# OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF
# ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
#

target=`getprop ro.board.platform`
low_ram=`getprop ro.config.low_ram`
if [ -f /sys/devices/soc0/soc_id ]; then
    platformid=`cat /sys/devices/soc0/soc_id`
else
    platformid=`cat /sys/devices/system/soc/soc0/id`
fi

start_battery_monitor()
{
	if ls /sys/bus/spmi/devices/qpnp-bms-*/fcc_data ; then
		chown -h root.system /sys/module/pm8921_bms/parameters/*
		chown -h root.system /sys/module/qpnp_bms/parameters/*
		chown -h root.system /sys/bus/spmi/devices/qpnp-bms-*/fcc_data
		chown -h root.system /sys/bus/spmi/devices/qpnp-bms-*/fcc_temp
		chown -h root.system /sys/bus/spmi/devices/qpnp-bms-*/fcc_chgcyl
		chmod 0660 /sys/module/qpnp_bms/parameters/*
		chmod 0660 /sys/module/pm8921_bms/parameters/*
		mkdir -p /data/bms
		chown -h root.system /data/bms
		chmod 0770 /data/bms
		start battery_monitor
	fi
}

start_charger_monitor()
{
	if ls /sys/module/qpnp_charger/parameters/charger_monitor; then
		chown -h root.system /sys/module/qpnp_charger/parameters/*
		chown -h root.system /sys/class/power_supply/battery/input_current_max
		chown -h root.system /sys/class/power_supply/battery/input_current_trim
		chown -h root.system /sys/class/power_supply/battery/input_current_settled
		chown -h root.system /sys/class/power_supply/battery/voltage_min
		chmod 0664 /sys/class/power_supply/battery/input_current_max
		chmod 0664 /sys/class/power_supply/battery/input_current_trim
		chmod 0664 /sys/class/power_supply/battery/input_current_settled
		chmod 0664 /sys/class/power_supply/battery/voltage_min
		chmod 0664 /sys/module/qpnp_charger/parameters/charger_monitor
		start charger_monitor
	fi
}

start_vm_bms()
{
	if [ -e /dev/vm_bms ]; then
		chown -h root.system /sys/class/power_supply/bms/current_now
		chown -h root.system /sys/class/power_supply/bms/voltage_ocv
		chmod 0664 /sys/class/power_supply/bms/current_now
		chmod 0664 /sys/class/power_supply/bms/voltage_ocv
		start vm_bms
	fi
}

start_msm_irqbalance_8939()
{
	if [ -f /vendor/bin/msm_irqbalance ]; then
		case "$platformid" in
		    "239" | "293" | "294" | "295" | "304" | "338" | "313" | "353" | "354")
			start vendor.msm_irqbalance;;
		    "349" | "350" )
			start vendor.msm_irqbal_lb;;
		esac
	fi
}

start_msm_irqbalance_msmnile()
{
         if [ -f /vendor/bin/msm_irqbalance ]; then
                start vendor.msm_irqbalance
         fi
}

start_msm_irqbalance_kona()
{
         if [ -f /vendor/bin/msm_irqbalance ]; then
                start vendor.msm_irqbalance
         fi
}

start_msm_irqbalance_lito()
{
         if [ -f /vendor/bin/msm_irqbalance ]; then
                start vendor.msm_irqbalance
         fi
}

start_msm_irqbalance_atoll()
{
         if [ -f /vendor/bin/msm_irqbalance ]; then
                start vendor.msm_irqbalance
         fi
}

start_msm_irqbalance660()
{
	if [ -f /vendor/bin/msm_irqbalance ]; then
		case "$platformid" in
		    "317" | "321" | "324" | "325" | "326" | "336" | "345" | "346" | "360" | "393")
			start vendor.msm_irqbalance;;
		    "318" | "327" | "385")
			start vendor.msm_irqbl_sdm630;;
		esac
	fi
}

start_msm_irqbalance()
{
	if [ -f /vendor/bin/msm_irqbalance ]; then
			start vendor.msm_irqbalance
	fi
}

baseband=`getprop ro.baseband`
echo 1 > /proc/sys/net/ipv6/conf/default/accept_ra_defrtr

case "$baseband" in
        "svlte2a")
        start bridgemgrd
        ;;
esac

case "$target" in
    "msm7630_surf" | "msm7630_1x" | "msm7630_fusion")
        if [ -f /sys/devices/soc0/hw_platform ]; then
            value=`cat /sys/devices/soc0/hw_platform`
        else
            value=`cat /sys/devices/system/soc/soc0/hw_platform`
        fi
        case "$value" in
            "Fluid")
             start profiler_daemon;;
        esac
        ;;
    "msm8660" )
        if [ -f /sys/devices/soc0/hw_platform ]; then
            platformvalue=`cat /sys/devices/soc0/hw_platform`
        else
            platformvalue=`cat /sys/devices/system/soc/soc0/hw_platform`
        fi
        case "$platformvalue" in
            "Fluid")
                start profiler_daemon;;
        esac
        ;;
    "msm8960")
        case "$baseband" in
            "msm")
                start_battery_monitor;;
        esac

        if [ -f /sys/devices/soc0/hw_platform ]; then
            platformvalue=`cat /sys/devices/soc0/hw_platform`
        else
            platformvalue=`cat /sys/devices/system/soc/soc0/hw_platform`
        fi
        case "$platformvalue" in
             "Fluid")
                 start profiler_daemon;;
             "Liquid")
                 start profiler_daemon;;
        esac
        ;;
    "msm8974")
        platformvalue=`cat /sys/devices/soc0/hw_platform`
        case "$platformvalue" in
             "Fluid")
                 start profiler_daemon;;
             "Liquid")
                 start profiler_daemon;;
        esac
        case "$baseband" in
            "msm")
                start_battery_monitor
                ;;
        esac
        start_charger_monitor
        ;;
    "sdm660")
        if [ -f /sys/devices/soc0/soc_id ]; then
             soc_id=`cat /sys/devices/soc0/soc_id`
        else
             soc_id=`cat /sys/devices/system/soc/soc0/id`
        fi

        if [ -f /sys/devices/soc0/hw_platform ]; then
             hw_platform=`cat /sys/devices/soc0/hw_platform`
        else
             hw_platform=`cat /sys/devices/system/soc/soc0/hw_platform`
        fi

        case "$soc_id" in
             "317" | "324" | "325" | "326" | "318" | "327" )
                  case "$hw_platform" in
                       "Surf")
                                    setprop qemu.hw.mainkeys 0
                                    ;;
                       "MTP")
                                    setprop qemu.hw.mainkeys 0
                                    ;;
                       "RCM")
                                    setprop qemu.hw.mainkeys 0
                                    ;;
                       "QRD")
                                    setprop qemu.hw.mainkeys 0
                                    ;;
                  esac
                  ;;
       esac
        start_msm_irqbalance660
        ;;
    "apq8084")
        platformvalue=`cat /sys/devices/soc0/hw_platform`
        case "$platformvalue" in
             "Fluid")
                 start profiler_daemon;;
             "Liquid")
                 start profiler_daemon;;
        esac
        ;;
    "msm8226")
        start_charger_monitor
        ;;
    "msm8610")
        start_charger_monitor
        ;;
    "msm8916")
        start_vm_bms
        start_msm_irqbalance_8939
        if [ -f /sys/devices/soc0/soc_id ]; then
            soc_id=`cat /sys/devices/soc0/soc_id`
        else
            soc_id=`cat /sys/devices/system/soc/soc0/id`
        fi

        if [ -f /sys/devices/soc0/platform_subtype_id ]; then
             platform_subtype_id=`cat /sys/devices/soc0/platform_subtype_id`
        fi
        if [ -f /sys/devices/soc0/hw_platform ]; then
             hw_platform=`cat /sys/devices/soc0/hw_platform`
        fi
        case "$soc_id" in
             "239")
                  case "$hw_platform" in
                       "Surf")
                            case "$platform_subtype_id" in
                                 "1")
                                      setprop qemu.hw.mainkeys 0
                                      ;;
                            esac
                            ;;
                       "MTP")
                          case "$platform_subtype_id" in
                               "3")
                                    setprop qemu.hw.mainkeys 0
                                    ;;
                          esac
                          ;;
                  esac
                  ;;
        esac
        ;;
    "msm8994" | "msm8992" | "msm8998" | "apq8098_latv" | "sdm845" | "sdm710" | "qcs605" | "sm6150" | "trinket" | "bengal")
        start_msm_irqbalance
        ;;
    "msm8996")
        if [ -f /sys/devices/soc0/hw_platform ]; then
             hw_platform=`cat /sys/devices/soc0/hw_platform`
        fi
        case "$hw_platform" in
                "MTP" | "CDP")
                #Loop through the sysfs nodes and determine the correct sysfs to change the permission and ownership.
                        for count in 0 1 2 3 4 5 6 7 8 9 10
                        do
                                dir="/sys/devices/soc/75ba000.i2c/i2c-12/12-0020/input/input"$count
                                if [ -d "$dir" ]; then
                                     chmod 0660 $dir/secure_touch_enable
                                     chmod 0440 $dir/secure_touch
                                     chown system.drmrpc $dir/secure_touch_enable
                                     chown system.drmrpc $dir/secure_touch
                                     break
                                fi
                        done
                        ;;
        esac
        ;;
    "msm8909")
        start_vm_bms
        ;;
    "msmnile")
        start_msm_irqbalance_msmnile
        ;;
    "kona")
        start_msm_irqbalance_kona
        ;;
    "lito")
        start_msm_irqbalance_lito
        ;;
    "atoll")
        start_msm_irqbalance_atoll
        ;;
    "msm8937")
        start_msm_irqbalance_8939
        if [ -f /sys/devices/soc0/soc_id ]; then
            soc_id=`cat /sys/devices/soc0/soc_id`
        else
            soc_id=`cat /sys/devices/system/soc/soc0/id`
        fi

        if [ -f /sys/devices/soc0/hw_platform ]; then
             hw_platform=`cat /sys/devices/soc0/hw_platform`
        else
             hw_platform=`cat /sys/devices/system/soc/soc0/hw_platform`
        fi
	if [ "$low_ram" != "true" ]; then
             case "$soc_id" in
                  "294" | "295" | "303" | "307" | "308" | "309" | "313" | "320" | "353" | "354" | "363" | "364")
                       case "$hw_platform" in
                            "Surf")
                                    setprop qemu.hw.mainkeys 0
                                    ;;
                            "MTP")
                                    setprop qemu.hw.mainkeys 0
                                    ;;
                            "RCM")
                                    setprop qemu.hw.mainkeys 0
                                    ;;
                            "QRD")
                                    setprop qemu.hw.mainkeys 0
                                    ;;
                       esac
                       ;;
             esac
        fi
        ;;
    "msm8953")
	start_msm_irqbalance_8939
        if [ -f /sys/devices/soc0/soc_id ]; then
            soc_id=`cat /sys/devices/soc0/soc_id`
        else
            soc_id=`cat /sys/devices/system/soc/soc0/id`
        fi

        if [ -f /sys/devices/soc0/hw_platform ]; then
             hw_platform=`cat /sys/devices/soc0/hw_platform`
        else
             hw_platform=`cat /sys/devices/system/soc/soc0/hw_platform`
        fi
        case "$soc_id" in
             "293" | "304" | "338" | "351" | "349" | "350" )
                  case "$hw_platform" in
                       "Surf")
                                    setprop qemu.hw.mainkeys 0
                                    ;;
                       "MTP")
                                    setprop qemu.hw.mainkeys 0
                                    ;;
                       "RCM")
                                    setprop qemu.hw.mainkeys 0
                                    ;;
                       "QRD")
                                    setprop qemu.hw.mainkeys 0
                                    ;;
                  esac
                  ;;
       esac
        ;;
    "sdm710")
        if [ -f /sys/devices/soc0/soc_id ]; then
            soc_id=`cat /sys/devices/soc0/soc_id`
        else
            soc_id=`cat /sys/devices/system/soc/soc0/id`
        fi

        if [ -f /sys/devices/soc0/hw_platform ]; then
             hw_platform=`cat /sys/devices/soc0/hw_platform`
        else
             hw_platform=`cat /sys/devices/system/soc/soc0/hw_platform`
        fi
        case "$soc_id" in
             "336" | "337" | "347" | "360" | "393" )
                  case "$hw_platform" in
                       "Surf")
                                    setprop qemu.hw.mainkeys 0
                                    ;;
                       "MTP")
                                    setprop qemu.hw.mainkeys 0
                                    ;;
                       "RCM")
                                    setprop qemu.hw.mainkeys 0
                                    ;;
                       "QRD")
                                    setprop qemu.hw.mainkeys 0
                                    ;;
                  esac
                  ;;
       esac
        ;;
esac

#
# Make modem config folder and copy firmware config to that folder for RIL
#
copy_modem_config() (
    firmware=/vendor/firmware_mnt
    modem_config=/data/vendor/modem_config
    version_file="$firmware/verinfo/ver_info.txt"
    [ -s "$version_file" ] || exit 1

    if ! cmp -s "$version_file" "$modem_config/ver_info.txt"; then
        chmod -R g+w "$modem_config" || exit 1
        rm -rf "$modem_config"/* || exit 1
        cp --preserve=m -dr "$firmware"/image/modem_pr/mcfg/configs/* "$modem_config" || exit 1
        if [ -f "$firmware/image/modem_pr/mbn_ota.txt" ]; then
            cp --preserve=m -d "$firmware/image/modem_pr/mbn_ota.txt" "$modem_config" || exit 1
        fi
        chown -hR radio.root "$modem_config"/* || exit 1
        # Publish the version only after the copied files are ready for QCRIL.
        version_tmp="$modem_config/ver_info.txt.tmp"
        cp --preserve=m -d "$version_file" "$version_tmp" || exit 1
        chown radio.root "$version_tmp" || exit 1
        mv -f "$version_tmp" "$modem_config/ver_info.txt" || exit 1
    fi
    chmod g-w "$modem_config"
)

if copy_modem_config; then
    setprop ro.vendor.ril.mbn_copy_completed 1
else
    log -t init.qcom.sh "Modem configuration copy failed"
fi

#check build variant for printk logging
#current default minimum boot-time-default
buildvariant=`getprop ro.build.type`
case "$buildvariant" in
    "userdebug" | "eng")
        #set default loglevel to KERN_INFO
        echo "6 6 1 7" > /proc/sys/kernel/printk
        ;;
    *)
        #set default loglevel to KERN_WARNING
        echo "4 4 1 4" > /proc/sys/kernel/printk
        ;;
esac

#ifdef NT_EDIT
# add for ARBOK-109: read the hwid from driver and setprop
# example as: cat proc/hwid = "version = EVB            gpio3_id1_adc=59mV  gpio4_id0_adc=59mV"
# persist.vendor.fastrpc.hwid_version = EVB
PROD_PROP=`getprop ro.product.name`
if [ "$PROD_PROP" = "Metroid" ];then
    if [ -f /proc/hwid ]; then
        originhwid=`cat /proc/hwid`
        hwid=`echo ${originhwid:10:13}`
        case "$hwid" in
                       "EVB")       setprop persist.vendor.fastrpc.hwid_version EVB
                                    ;;
                       "T0")
                                    setprop persist.vendor.fastrpc.hwid_version T0
                                    ;;
                       "T0_Felica")
                                    setprop persist.vendor.fastrpc.hwid_version T0_Felica
                                    ;;
                       "EVT")
                                    setprop persist.vendor.fastrpc.hwid_version EVT
                                    ;;
                       "EVT_Felica")
                                    setprop persist.vendor.fastrpc.hwid_version EVT_Felica
                                    ;;
                       "EVT_Power")
                                    setprop persist.vendor.fastrpc.hwid_version EVT_Power
                                    ;;
                       "EVT_CS")
                                    setprop persist.vendor.fastrpc.hwid_version EVT_CS
                                    ;;
                       "EVT_Felica_CS")
                                    setprop persist.vendor.fastrpc.hwid_version EVT_Felica_CS
                                    ;;
                       "DVT")
                                    setprop persist.vendor.fastrpc.hwid_version DVT
                                    ;;
                       "DVT_Felica")
                                    setprop persist.vendor.fastrpc.hwid_version DVT_Felica
                                    ;;
                       "PVT")
                                    setprop persist.vendor.fastrpc.hwid_version PVT
                                    ;;
                       "PVT_Felica")
                                    setprop persist.vendor.fastrpc.hwid_version PVT_Felica
                                    ;;
        esac
    fi
fi

if [ "$PROD_PROP" = "FroggerPro" -o "$PROD_PROP" = "lineage_FroggerPro" ];then
    if [ -f /proc/hwid ]; then
        originhwid=`cat /proc/hwid`
        hwid=`echo $originhwid | awk '{print $3}'`
        case "$hwid" in
		       "P0")       setprop persist.vendor.fastrpc.hwid_version P0
                                    ;;
                       "PreT0")       setprop persist.vendor.fastrpc.hwid_version PreT0
                                    ;;
                       "T0")
                                    setprop persist.vendor.fastrpc.hwid_version T0
                                    ;;
                       "EVT")
                                    setprop persist.vendor.fastrpc.hwid_version EVT
                                    ;;
                       "DVT")
                                    setprop persist.vendor.fastrpc.hwid_version DVT
                                    ;;
                       "PVT")
                                    setprop persist.vendor.fastrpc.hwid_version PVT
                                    ;;
                       "POWER_BOARD")
                                    setprop persist.vendor.fastrpc.hwid_version POWER_BOARD
                                    ;;
                       "T0_India")
                                    setprop persist.vendor.fastrpc.hwid_version T0_India
                                    ;;
                       "EVT_India")
                                    setprop persist.vendor.fastrpc.hwid_version EVT_India
                                    ;;
                       "DVT_India")
                                    setprop persist.vendor.fastrpc.hwid_version DVT_India
                                    ;;
                       "PVT_India")
                                    setprop persist.vendor.fastrpc.hwid_version PVT_India
                                    ;;
		       "T0_Japan")
                                    setprop persist.vendor.fastrpc.hwid_version T0_Japan
                                    ;;
                       "EVT_Japan")
                                    setprop persist.vendor.fastrpc.hwid_version EVT_Japan
                                    ;;
		       "DVT_Japan")
                                    setprop persist.vendor.fastrpc.hwid_version DVT_Japan
                                    ;;
                       "PVT_Japan")
                                    setprop persist.vendor.fastrpc.hwid_version PVT_Japan
				    ;;
           	       "Unknow")
                                    setprop persist.vendor.fastrpc.hwid_version Unknow
                                    ;;
	esac
    fi
fi
#endif NT_EDIT
