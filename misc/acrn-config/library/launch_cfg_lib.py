# Copyright (C) 2019 Intel Corporation. All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause
#

import os
import getopt
import common
import board_cfg_lib

ERR_LIST = {}
BOOT_TYPE = ['no', 'vsbl', 'ovmf']
RTOS_TYPE = ['no', 'Soft RT', 'Hard RT']
DM_VUART0 = ['Disable', 'Enable']
CPU_SHARING = ['Disabled', 'Enabled']
UOS_TYPES = ['CLEARLINUX', 'ANDROID', 'ALIOS', 'PREEMPT-RT LINUX', 'VXWORKS', 'WINDOWS', 'ZEPHYR', 'GENERIC LINUX']

PT_SUB_PCI = {}
PT_SUB_PCI['usb_xdci'] = ['USB controller']
PT_SUB_PCI['ipu'] = ['Multimedia controller']
PT_SUB_PCI['ipu_i2c'] = ['Signal processing controller']
PT_SUB_PCI['cse'] = ['Communication controller']
PT_SUB_PCI['audio'] = ['Audio device', 'Multimedia audio controller']
PT_SUB_PCI['audio_codec'] = ['Signal processing controller']
PT_SUB_PCI['sd_card'] = ['SD Host controller']
PT_SUB_PCI['wifi'] = ['Ethernet controller', 'Network controller', '802.1a controller',
                        '802.1b controller', 'Wireless controller']
PT_SUB_PCI['bluetooth'] = ['Signal processing controller']
PT_SUB_PCI['ethernet'] = ['Ethernet controller', 'Network controller']
PT_SUB_PCI['sata'] = ['SATA controller']
PT_SUB_PCI['nvme'] = ['Non-Volatile memory controller']

# passthrough devices for board
PASSTHRU_DEVS = ['usb_xdci', 'ipu', 'ipu_i2c', 'cse', 'audio', 'sata',
                    'nvme', 'audio_codec', 'sd_card', 'ethernet', 'wifi', 'bluetooth']

PT_SLOT = {
        "hostbridge":0,
        "lpc":1,
        "pci-gvt":2,
        "virtio-blk":3,
        "audio_codec":24
    }


POST_UUID_DIC = {}
PM_CHANNEL = ['', 'IOC', 'PowerButton', 'vuart1(pty)', 'vuart1(tty)']
PM_CHANNEL_DIC = {
    None:'',
    'IOC':'--pm_notify_channel ioc',
    'PowerButton':'--pm_notify_channel power_button',
    'vuart1(pty)':'--pm_notify_channel uart \\\n   --pm_by_vuart pty,/run/acrn/life_mngr_$vm_name \\\n   -l com2,/run/acrn/life_mngr_$vm_name',
    'vuart1(tty)':'--pm_notify_channel uart --pm_by_vuart tty,/dev/ttyS1',
}

MOUNT_FLAG_DIC = {}


def usage(file_name):
    """ This is usage for how to use this tool """
    print("usage= {} [h]".format(file_name), end="")
    print("--board <board_info_file> --scenario <scenario_info_file> --launch <launch_info_file> --uosid <uosid id> --out [output folder]")
    print('board_info_file :  file name of the board info')
    print('scenario_info_file :  file name of the scenario info')
    print('launch_info_file :  file name of the launch info')
    print('uosid :  this is the relateive id for post launch vm in scenario info XML:[1..max post launch vm]')
    print('output folder :  path to acrn-hypervisor_folder')


def get_param(args):
    """
    Get the script parameters from command line
    :param args: this the command line of string for the script without script name
    """
    vm_th = '0'
    err_dic = {}
    board_info_file = False
    scenario_info_file = False
    launch_info_file = False
    output_folder = False
    param_list = ['--board', '--scenario', '--launch', '--uosid']

    for arg_str in param_list:

        if arg_str not in args:
            usage(args[0])
            err_dic['common error: get wrong parameter'] = "wrong usage"
            return (err_dic, board_info_file, scenario_info_file, launch_info_file, int(vm_th), output_folder)

    args_list = args[1:]
    (optlist, args_list) = getopt.getopt(args_list, '', ['board=', 'scenario=', 'launch=', 'uosid=', 'out='])
    for arg_k, arg_v in optlist:
        if arg_k == '--board':
            board_info_file = arg_v
        if arg_k == '--scenario':
            scenario_info_file = arg_v
        if arg_k == '--launch':
            launch_info_file = arg_v
        if arg_k == '--out':
            output_folder = arg_v
        if '--uosid' in args:
            if arg_k == '--uosid':
                vm_th = arg_v
                if not vm_th.isnumeric():
                    err_dic['common error: get wrong parameter'] = "--uosid should be a number"
                    return (err_dic, board_info_file, scenario_info_file, launch_info_file, int(vm_th), output_folder)

    if not board_info_file or not scenario_info_file or not launch_info_file:
        usage(args[0])
        err_dic['common error: get wrong parameter'] = "wrong usage"
        return (err_dic, board_info_file, scenario_info_file, launch_info_file, int(vm_th), output_folder)

    if not os.path.exists(board_info_file):
        err_dic['common error: get wrong parameter'] = "{} is not exist!".format(board_info_file)
        return (err_dic, board_info_file, scenario_info_file, launch_info_file, int(vm_th), output_folder)

    if not os.path.exists(scenario_info_file):
        err_dic['common error: get wrong parameter'] = "{} is not exist!".format(scenario_info_file)
        return (err_dic, board_info_file, scenario_info_file, launch_info_file, int(vm_th), output_folder)

    if not os.path.exists(launch_info_file):
        err_dic['common error: get wrong parameter'] = "{} is not exist!".format(launch_info_file)
        return (err_dic, board_info_file, scenario_info_file, launch_info_file, int(vm_th), output_folder)

    return (err_dic, board_info_file, scenario_info_file, launch_info_file, int(vm_th), output_folder)


def launch_vm_cnt(config_file):
    """
    Get post vm number
    :param config_file: it is a file what contains information for script to read from
    :return: total post vm number in launch file
    """
    post_vm_count = 0

    # get post vm number
    root = common.get_config_root(config_file)
    for item in root:
        if item.tag == "uos":
            post_vm_count += 1

    return post_vm_count


def get_post_num_list():
    """
    Get post vm number list
    :return: total post dic: {launch_id:scenario_id} in launch file
    """
    post_vm_list = []

    # get post vm number
    root = common.get_config_root(common.LAUNCH_INFO_FILE)
    for item in root:
        if item.tag == "uos":
            post_vm_list.append(int(item.attrib['id']))

    return post_vm_list


def post_vm_cnt(config_file):
    """
    Calculate the pre launched vm number
    :param config_file: it is a file what contains information for script to read from
    :return: number of post launched vm
    """
    post_launch_cnt = 0
    load_type_list = common.get_sub_leaf_tag(config_file, "load_order")

    for vm_type in load_type_list:
        if vm_type == "POST_LAUNCHED_VM":
            post_launch_cnt += 1

    return post_launch_cnt


def get_post_vm_cnt():
    """
    Get board name from launch.xml at fist line
    :param scenario_file: it is a file what contains scenario information for script to read from
    """
    launch_vm_count = launch_vm_cnt(common.LAUNCH_INFO_FILE)
    post_vm_count = post_vm_cnt(common.SCENARIO_INFO_FILE)
    return (launch_vm_count, post_vm_count)


def get_avl_dev_info(bdf_desc_map, pci_sub_class):

    tmp_pci_desc = []
    for sub_class in pci_sub_class:
        for pci_desc_value in bdf_desc_map.values():
            pci_desc_sub_class = ' '.join(pci_desc_value.strip().split(':')[1].split()[1:])
            if sub_class == pci_desc_sub_class:
                tmp_pci_desc.append(pci_desc_value.strip())

    return tmp_pci_desc


def is_config_file_match():

    match = True
    # check if the board config match scenario config
    (err_dic, scenario_for_board) = common.get_xml_attrib(common.SCENARIO_INFO_FILE, "board")
    (err_dic, board_name) = common.get_xml_attrib(common.BOARD_INFO_FILE, "board")
    if scenario_for_board != board_name:
        err_dic['scenario config: Not match'] = "The board xml and scenario xml should be matched!"
        match = False

    # check if the board config match launch config
    (err_dic, launch_for_board) = common.get_xml_attrib(common.LAUNCH_INFO_FILE, "board")
    if launch_for_board != board_name:
        err_dic['launch config: Not match'] = "The board xml and launch xml should be matched!"
        match = False

    return (err_dic, match)


def get_scenario_uuid():
    # {id_num:uuid} (id_num:0~max)
    scenario_uuid_dic = {}
    scenario_uuid_dic = common.get_leaf_tag_map(common.SCENARIO_INFO_FILE, 'uuid')
    return scenario_uuid_dic


def get_sos_vmid():

    load_dic = common.get_leaf_tag_map(common.SCENARIO_INFO_FILE, "load_order")

    sos_id = ''
    for idx,load_order in load_dic.items():
        if load_order == "SOS_VM":
            sos_id = idx
            break

    return sos_id


def get_bdf_from_tag(config_file, branch_tag, tag_str):
    bdf_list = {}
    bdf_list = common.get_leaf_tag_map(config_file, branch_tag, tag_str)

    # split b:d:f from pci description
    for idx, bdf_v in bdf_list.items():
        if bdf_v:
            bdf_list[idx] = bdf_v.split()[0]

    return bdf_list


def get_vpid_from_bdf(bdf_vpid_map, bdf_list):
    vpid_list = {}
    post_vm_list = get_post_num_list()
    for p_id in post_vm_list:
        for bdf_k, vpid_v in bdf_vpid_map.items():
            if bdf_k == bdf_list[p_id]:
                #    print("k:{}, v{}".format(bdf_k, bdf_list[p_id]))
                # convert "808x:0xxx" to "808x 0xxx"
                tmp_vpid = " ".join(vpid_v.split(':'))
                vpid_list[p_id] = tmp_vpid
            elif not bdf_list[p_id]:
                vpid_list[p_id] = ''

    return vpid_list


def get_uos_type():
    """
    Get uos name from launch.xml at fist line
    """
    uos_types = common.get_leaf_tag_map(common.LAUNCH_INFO_FILE, "uos_type")

    return uos_types


def is_bdf_format(bdf_str):
    bdf_len = 7
    status = True
    if not bdf_str:
        return status

    bdf_str_len = len(bdf_str)
    if ':' in bdf_str and '.' in bdf_str and bdf_len == bdf_str_len:
        status = True
    else:
        status = False

    return status


def is_vpid_format(vpid_str):
    status = True
    if not vpid_str:
        return status

    vpid_len = 9
    vpid_str_len = len(vpid_str)

    if ' ' in vpid_str and vpid_len == vpid_str_len:
        status = True
    else:
        status = False

    return status


def pt_devs_check(bdf_list, vpid_list, item):
    i_cnt = 1

    # check bdf
    for bdf_str in bdf_list.values():
        if is_bdf_format(bdf_str):
            continue
        else:
            key = "uos:id={},passthrough_devices,{}".format(i_cnt, item)
            ERR_LIST[key] = "Unkonw the BDF format of {} device".format(item)
        i_cnt += 1

    # check vpid
    i_cnt = 1
    for vpid_str in vpid_list.values():
        if is_vpid_format(vpid_str):
            continue
        else:
            key = "uos:id={},passthrough_devices,{}".format(i_cnt, item)
            ERR_LIST[key] = "Unkonw the Vendor:Product ID format of {} device".format(item)

        i_cnt += 1


def empty_err(i_cnt, item):
    """
    add empty error message into ERR_LIST
    :param i_cnt: the launch vm index from config xml
    :param item: the item of tag from config xml
    :return: None
    """
    key = "uos:id={},{}".format(i_cnt, item)
    ERR_LIST[key] = "The parameter should not be empty"


def args_aval_check(arg_list, item, avl_list):
    """
    check arguments from config xml are available and validate
    :param arg_list: the list of arguments from config xml
    :param item: the item of tag from config xml
    :param avl_list: available argument which are allowed to chose
    :return: None
    """
    # args should be set into launch xml from webUI
    i_cnt = 1
    skip_check_list = ['']
    if item in skip_check_list:
        return

    for arg_str in arg_list.values():
        if arg_str == None or not arg_str.strip():
            empty_err(i_cnt, item)
            i_cnt += 1
            continue

        if arg_str not in avl_list:
            key = "uos:id={},{}".format(i_cnt, item)
            ERR_LIST[key] = "The {} is invalidate".format(item)
        i_cnt += 1


def mem_size_check(arg_list, item):
    """
     check memory size list which are set from webUI
     :param arg_list: the list of arguments from config xml
     :param item: the item of tag from config xml
     :return: None
     """
    # get total memory information
    total_mem_mb = board_cfg_lib.get_total_mem()

    # available check
    i_cnt = 1
    for arg_str in arg_list.values():
        if arg_str == None or not arg_str.strip():
            empty_err(i_cnt, item)
            i_cnt += 1
            continue

        mem_size_set = int(arg_str.strip())
        if mem_size_set > total_mem_mb:
            key = "uos:id={},{}".format(i_cnt, item)
            ERR_LIST[key] = "{}MB should be less than total memory {}MB".format(item)
        i_cnt += 1


def virtual_dev_slot(dev):
    max_slot = 31
    base_slot = 3

    # get devices slot which already stored
    if dev in list(PT_SLOT.keys()):
        return PT_SLOT[dev]

    # alloc a new slot for device
    for slot_num in range(base_slot, max_slot):
        if slot_num not in list(PT_SLOT.values()):

            if (slot_num == 6 and 14 in list(PT_SLOT.values())) or (slot_num == 14 and 6 in list(PT_SLOT.values())):
                continue
            if (slot_num == 7 and 15 in list(PT_SLOT.values())) or (slot_num == 15 and 7 in list(PT_SLOT.values())):
                continue

            PT_SLOT[dev] = slot_num
            break

    return slot_num


def get_slot(bdf_list, dev):

    slot_list = {}
    post_vm_list = get_post_num_list()
    for p_id in post_vm_list:
        if not bdf_list[p_id]:
            slot_list[p_id] = ''
        else:
            bus = int(bdf_list[p_id][0:2], 16)
            slot = int(bdf_list[p_id][3:5], 16)
            fun = int(bdf_list[p_id][6:7], 16)
            slot_fun = str(bus) + ":" +  str(slot) + ":" + str(fun)
            if bus != 0:
                slot_fun = virtual_dev_slot(dev)
                PT_SLOT[dev] = slot_fun
            else:
                # add already used slot for pass-throught devices to avoid conflict with virtio devices
                PT_SLOT[dev] = slot

            slot_list[p_id] = slot_fun

    return slot_list


def get_pt_dev():
    """ Get passthrough device list """
    cap_pt = PASSTHRU_DEVS

    return cap_pt


def get_vuart1_from_scenario(vmid):
    """Get the vmid's  vuart1 base"""
    vuart1 = board_cfg_lib.get_vuart_info_id(common.SCENARIO_INFO_FILE, 1)
    return vuart1[vmid]['base']


def pt_devs_check_audio(audio_map, audio_codec_map):
    """
    Check the connections about audio/audio_codec pass-through devices
    If audio_codec is selected as pass-through device, the audio device
    must to be chosen as pass-through device either.
    :param audio_map: the dictionary contains vmid and bdf of audio device
    :param audio_codec_map: the dictionary contains vmid and bdf of audio_codec device
    """
    for vmid in list(audio_map.keys()):
        bdf_audio = audio_map[vmid]
        bdf_codec = audio_codec_map[vmid]
        if not bdf_audio and bdf_codec:
            key = "uos:id={},passthrough_devices,{}".format(vmid, 'audio_codec')
            ERR_LIST[key] = "Audio codec device should be pass through together with Audio devcie!"


def check_block_mount(virtio_blk_dic):
    blk_dev_list = board_cfg_lib.get_rootfs(common.BOARD_INFO_FILE)
    for vmid in list(virtio_blk_dic.keys()):
        mount_flags = []
        for blk in virtio_blk_dic[vmid]:
            rootfs_img = ''
            if not blk:
                mount_flags.append(False)
                continue

            if ':' in blk:
                blk_dev = blk.split(':')[0]
                rootfs_img = blk.split(':')[1]
            else:
                blk_dev = blk

            if blk_dev in blk_dev_list and rootfs_img:
                mount_flags.append(True)
            else:
                mount_flags.append(False)

        MOUNT_FLAG_DIC[vmid] = mount_flags


def cpu_sharing_check(cpu_sharing, item):
    """
    Check cpu sharing status with cpu affinity setting
    :param cpu_share_status:
    :param item:
    :return: None
    """
    use_cpus = []
    use_same_cpu = False
    vm_cpu_share = []
    vm_cpu_share_consistent = True

    cpu_affinity = common.get_leaf_tag_map(common.SCENARIO_INFO_FILE, "vcpu_affinity", "pcpu_id")
    for vm_i in cpu_affinity.keys():
        for cpu in cpu_affinity[vm_i]:
            if cpu in use_cpus:
                use_same_cpu = True
            else:
                use_cpus.append(cpu)

    for vm_i in cpu_sharing.keys():
        cpu_share = cpu_sharing[vm_i]
        stat_len = len(vm_cpu_share)
        if stat_len != 0 and cpu_share not in vm_cpu_share:
            vm_cpu_share_consistent = False
        else:
            vm_cpu_share.append(cpu_share)

        if not vm_cpu_share_consistent:
            key = "uos:id={},{}".format(vm_i, item)
            ERR_LIST[key] = "CPU sharing for all VMs should be consistent to 'Disabled' or 'Enabled'"
            return

        if cpu_sharing[vm_i] == "Disabled" and use_same_cpu:
            key = "uos:id={},{}".format(vm_i, item)
            ERR_LIST[key] = "The same pcpu was configurated in scenario config, and not allow to set the cpu_sharing to 'Disabled'!"
            return


def bdf_duplicate_check(bdf_dic):
    """
    Check if exist duplicate slot
    :param bdf_dic: contains all selected pass-through devices
    :return: None
    """
    bdf_used = []
    for dev in bdf_dic.keys():
        dev_bdf_dic = bdf_dic[dev]
        for vm_i in dev_bdf_dic.keys():
            dev_bdf = dev_bdf_dic[vm_i]
            if not dev_bdf:
                continue

            if dev_bdf in bdf_used:
                key = "uos:id={},{},{}".format(vm_i, 'passthrough_devices', dev)
                ERR_LIST[key] = "You select the same device for {} pass-through !".format(dev)
                return
            else:
                bdf_used.append(dev_bdf)
