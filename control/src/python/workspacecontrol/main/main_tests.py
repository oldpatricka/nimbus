import optparse
import os
import shutil
import sys

import wc_optparse
import workspacecontrol.api.modules as modules
import workspacecontrol.api.objects as objects
from workspacecontrol.main import get_class_by_keyword
from workspacecontrol.api.exceptions import *
from main_tests_util import mockconfigs, get_pc, realconfigs

# -----------------------------------------------------------------------------

def test_getallconfigs():
    """Test if the configuration setup is sane"""
    platform_cls = get_class_by_keyword("Platform", allconfigs=mockconfigs())
    assert modules.IPlatform.implementedBy(platform_cls)
    
def test_logging():
    """Test if the logging setup is sane"""
    p,c = get_pc(None, mockconfigs())
    c.log.debug("test_logging()")
    
def test_cmdline_parameters():
    """Test cmdline parameter intake error"""
    parser = wc_optparse.parsersetup()
    exc_thrown = False
    tmp = sys.stderr
    sys.stderr = sys.stdout
    try:
        # requires argument, should fail:
        (opts, args) = parser.parse_args(["--action"])
    except SystemExit:
        exc_thrown = True
    assert exc_thrown
    sys.stderr = tmp
    
def test_cmdline_parameters2():
    """Test cmdline parameter intake success"""
    parser = wc_optparse.parsersetup()
    (opts, args) = parser.parse_args(["-a", "create"])
    assert opts.action != None
    
def test_cmdline_parameters3():
    """Test cmdline parameter intake booleans"""
    parser = wc_optparse.parsersetup()
    (opts, args) = parser.parse_args(["-a", "create", "--startpaused"])
    assert opts.startpaused == True
    
    (opts, args) = parser.parse_args(["-a", "create"])
    assert opts.startpaused == False
    
def test_mock_procurement():
    """Test the procurement test adapter interaction"""
    
    p,c = get_pc(None, mockconfigs())
    c.log.debug("test_mock_procurement()")
    
    procure_cls = c.get_class_by_keyword("ImageProcurement")
    procure = procure_cls(p, c)
    procure.validate()
    local_file_set = procure.obtain()
    
    for lf in local_file_set.flist():
        assert lf.path
        assert lf.mountpoint
        assert os.access(lf.path, os.F_OK)
        
    procure.process_after_destroy(local_file_set)
    
def test_mock_network_lease():
    """Test the network lease test adapter interaction"""
    
    p,c = get_pc(None, mockconfigs())
    c.log.debug("test_mock_network_lease()")
    
    netlease_cls = c.get_class_by_keyword("NetworkLease")
    netlease = netlease_cls(p, c)
    netlease.validate()
    nic = netlease.obtain("public")
    
    assert nic.network == "public"
    
    nicset_cls = c.get_class_by_keyword("NICSet")
    nic_set = nicset_cls([nic])
    
    netlease.release(nic_set)
    
def test_kernel1():
    """Test the kernel adapter basics"""
    
    p,c = get_pc(None, mockconfigs())
    c.log.debug("test_kernel1()")
    
    kernelpr_cls = c.get_class_by_keyword("KernelProcurement")
    kernelprocure = kernelpr_cls(p,c)
    kernelprocure.validate()
    
def test_kernel2():
    """Test the kernel adapter obtain() with mock images"""
    
    p,c = get_pc(None, mockconfigs())
    c.log.debug("test_kernel2()")
    
    kernelpr_cls = c.get_class_by_keyword("KernelProcurement")
    kernelprocure = kernelpr_cls(p,c)
    kernelprocure.validate()
    
    procure_cls = c.get_class_by_keyword("ImageProcurement")
    procure = procure_cls(p, c)
    procure.validate()
    local_file_set = procure.obtain()
    
    kernel = kernelprocure.kernel_files(local_file_set)
    assert kernel
    
    # use providedBy on instances (implementedBy is for classes)
    assert objects.IKernel.providedBy(kernel)
    
    # clean up
    procure.process_after_destroy(local_file_set)
    
def test_mock_create():
    """Test the create command with the libvirt mock adapter"""
    
    handle = "wrksp-393"
    createargs = ["--action", "create", 
                  "--name", handle,
                  "--memory", "256",
                 ]
    parser = wc_optparse.parsersetup()
    (opts, args) = parser.parse_args(createargs)
    
    p,c = get_pc(opts, mockconfigs())
    c.log.debug("test_mock_create()")
    
    procure_cls = c.get_class_by_keyword("ImageProcurement")
    procure = procure_cls(p, c)
    procure.validate()
    local_file_set = procure.obtain()
    
    kernelpr_cls = c.get_class_by_keyword("KernelProcurement")
    kernelprocure = kernelpr_cls(p,c)
    kernelprocure.validate()
    kernel = kernelprocure.kernel_files(local_file_set)
    
    netlease_cls = c.get_class_by_keyword("NetworkLease")
    netlease = netlease_cls(p, c)
    netlease.validate()
    nic = netlease.obtain("public")
    nicset_cls = c.get_class_by_keyword("NICSet")
    nic_set = nicset_cls([nic])
    
    platform_cls = c.get_class_by_keyword("Platform")
    platform = platform_cls(p, c)
    platform.validate()
    platform.create(local_file_set, nic_set, kernel)

    running_vm = platform.info(handle)
    assert running_vm
    
    assert running_vm.wchandle == handle
    assert running_vm.maxmem == 256
    assert running_vm.curmem == 256
    assert running_vm.running
    assert not running_vm.blocked
    assert not running_vm.paused
    assert not running_vm.shutting_down
    assert not running_vm.shutoff
    assert not running_vm.crashed
    
    platform.destroy(running_vm)
    
    tmp = sys.stderr
    sys.stderr = sys.stdout
    running_vm = platform.info(handle)
    assert not running_vm
    sys.stderr = tmp
    
    # clean up
    procure.process_after_destroy(local_file_set)
    
def test_real_procurement_propagate1():
    """Test the procurement adapter propagate awareness (positive)"""
    
    handle = "wrksp-411"
    createargs = ["--action", "create", 
                  "--name", handle,
                  "--memory", "256",
                  "--images", "scp://somehost/some-base-cluster-01.gz",
                  "--imagemounts", "xvda1",
                 ]
    parser = wc_optparse.parsersetup()
    (opts, args) = parser.parse_args(createargs)
    
    p,c = get_pc(opts, realconfigs())
    c.log.debug("test_real_procurement_propagate1()")
    
    procure_cls = c.get_class_by_keyword("ImageProcurement")
    procure = procure_cls(p, c)
    procure.validate()
    assert procure.lengthy_obtain()
    
    
def _create_fake_securedir_files(p, c, handle, filelist):
    # Requires knowledge of the module implementation
    securelocaldir = p.get_conf_or_none("images", "securelocaldir")
    if not os.path.isabs(securelocaldir):
        securelocaldir = c.resolve_var_dir(securelocaldir)
    vmdir = os.path.join(securelocaldir, handle)
    if os.path.exists(vmdir):
        raise IncompatibleEnvironment("test vmdir already exists: %s" % vmdir)
    os.mkdir(vmdir)
    
    for relative_filename in filelist:
        path = os.path.join(vmdir, relative_filename)
        # touch file
        f = None
        try:
            f = open(path, 'w')
        finally:
            if f:
                f.close()
                del f
        c.log.debug("created zero byte file: %s" % path)
    
def _destroy_fake_securedir(p, c, handle):
    # Requires knowledge of the module implementation
    securelocaldir = p.get_conf_or_none("images", "securelocaldir")
    if not os.path.isabs(securelocaldir):
        securelocaldir = c.resolve_var_dir(securelocaldir)
    vmdir = os.path.join(securelocaldir, handle)
    if not os.path.exists(vmdir):
        raise IncompatibleEnvironment("test vmdir does not exist? %s" % vmdir)
    shutil.rmtree(vmdir)
    
def test_real_procurement_propagate2():
    """Test that a local file will not report propagation needed.
    """
    
    handle = "wrksp-412"
    relative_filename_testfile = "some-base-cluster-01.gz"
    createargs = ["--action", "create", 
                  "--name", handle,
                  "--memory", "256",
                  "--images", "file://%s" % relative_filename_testfile,
                  "--imagemounts", "xvda1",
                 ]
    parser = wc_optparse.parsersetup()
    (opts, args) = parser.parse_args(createargs)
    
    p,c = get_pc(opts, realconfigs())
    c.log.debug("test_real_procurement_propagate2()")
    
    procure_cls = c.get_class_by_keyword("ImageProcurement")
    procure = procure_cls(p, c)
    procure.validate()
    
    try:
        filelist = [relative_filename_testfile]
        _create_fake_securedir_files(p, c, handle, filelist)
        
        assert not procure.lengthy_obtain()
        
    finally:
        _destroy_fake_securedir(p, c, handle)
        
def test_real_procurement_propagate3():
    """Test that an unknown propagation scheme will cause an error.
    """
    
    handle = "wrksp-412"
    relative_filename_testfile = "some-base-cluster-01.gz"
    createargs = ["--action", "create", 
                  "--name", handle,
                  "--memory", "256",
                  "--images", "zzfile://%s" % relative_filename_testfile,
                  "--imagemounts", "xvda1",
                 ]
    parser = wc_optparse.parsersetup()
    (opts, args) = parser.parse_args(createargs)
    
    p,c = get_pc(opts, realconfigs())
    c.log.debug("test_real_procurement_propagate3()")
    
    procure_cls = c.get_class_by_keyword("ImageProcurement")
    procure = procure_cls(p, c)
    procure.validate()
    
    try:
        filelist = [relative_filename_testfile]
        _create_fake_securedir_files(p, c, handle, filelist)
        
        invalid_input = False
        try:
            procure.lengthy_obtain()
        except InvalidInput:
            invalid_input = True
        assert invalid_input
        
    finally:
        _destroy_fake_securedir(p, c, handle)
        
def test_real_procurement_propagate4():
    """Test that a remote scheme with an incomplete URL will cause an error.
    """
    
    handle = "wrksp-499"
    createargs = ["--action", "create", 
                  "--name", handle,
                  "--memory", "256",
                  "--images", "scp://somehostsome-base-cluster-01.gz",
                  "--imagemounts", "xvda1",
                 ]
    parser = wc_optparse.parsersetup()
    (opts, args) = parser.parse_args(createargs)
    
    p,c = get_pc(opts, realconfigs())
    c.log.debug("test_real_procurement_propagate4()")
    
    procure_cls = c.get_class_by_keyword("ImageProcurement")
    procure = procure_cls(p, c)
    procure.validate()
    
    invalid_input = False
    try:
        procure.lengthy_obtain()
    except InvalidInput:
        invalid_input = True
    assert invalid_input
    
def test_real_procurement_propagate5():
    """Test that a malformed input to the procurement adapter will cause an error
    """
    
    handle = "wrksp-499"
    createargs = ["--action", "create", 
                  "--name", handle,
                  "--memory", "256",
                  "--images", "scp://somehost/some-base-cluster-01.gz;;x",
                  "--imagemounts", "xvda1",
                 ]
    parser = wc_optparse.parsersetup()
    (opts, args) = parser.parse_args(createargs)
    
    p,c = get_pc(opts, realconfigs())
    c.log.debug("test_real_procurement_propagate5()")
    
    procure_cls = c.get_class_by_keyword("ImageProcurement")
    procure = procure_cls(p, c)
    procure.validate()
    
    invalid_input = False
    try:
        procure.lengthy_obtain()
    except InvalidInput:
        invalid_input = True
    assert invalid_input
    
def test_real_procurement_propagate6():
    """Test that multiple image inputs are OK
    """
    
    handle = "wrksp-499"
    createargs = ["--action", "create", 
                  "--name", handle,
                  "--memory", "256",
                  "--images", "scp://somehost/some-base-cluster-01.gz;;scp://someotherhost/someother-base-cluster-01.gz",
                  "--imagemounts", "xvda1;;xvda2",
                 ]
    parser = wc_optparse.parsersetup()
    (opts, args) = parser.parse_args(createargs)
    
    p,c = get_pc(opts, realconfigs())
    c.log.debug("test_real_procurement_propagate6()")
    
    procure_cls = c.get_class_by_keyword("ImageProcurement")
    procure = procure_cls(p, c)
    procure.validate()
    
    assert procure.lengthy_obtain()
    
def test_real_procurement_propagate7():
    """Test that a mismatch of images and mountpoints will cause an error
    """
    
    handle = "wrksp-499"
    createargs = ["--action", "create", 
                  "--name", handle,
                  "--memory", "256",
                  "--images", "scp://somehost/some-base-cluster-01.gz;;scp://someotherhost/someother-base-cluster-01.gz",
                  "--imagemounts", "xvda1",
                 ]
    parser = wc_optparse.parsersetup()
    (opts, args) = parser.parse_args(createargs)
    
    p,c = get_pc(opts, realconfigs())
    c.log.debug("test_real_procurement_propagate7()")
    
    procure_cls = c.get_class_by_keyword("ImageProcurement")
    procure = procure_cls(p, c)
    procure.validate()
    
    invalid_input = False
    try:
        procure.lengthy_obtain()
    except InvalidInput:
        invalid_input = True
    assert invalid_input
    
def test_real_procurement_propagate8():
    """Test that a mismatch of images and mountpoints will cause an error
    """
    
    handle = "wrksp-499"
    createargs = ["--action", "create", 
                  "--name", handle,
                  "--memory", "256",
                  "--images", "scp://somehost/some-base-cluster-01.gz",
                  "--imagemounts", "xvda1;;xvda2",
                 ]
    parser = wc_optparse.parsersetup()
    (opts, args) = parser.parse_args(createargs)
    
    p,c = get_pc(opts, realconfigs())
    c.log.debug("test_real_procurement_propagate8()")
    
    procure_cls = c.get_class_by_keyword("ImageProcurement")
    procure = procure_cls(p, c)
    procure.validate()
    
    invalid_input = False
    try:
        procure.lengthy_obtain()
    except InvalidInput:
        invalid_input = True
    assert invalid_input
    
def test_real_procurement_unpropagate1():
    """Test the procurement adapter unpropagate awareness (positive)"""
    
    handle = "wrksp-2133"
    createargs = ["--action", "unpropagate", 
                  "--name", handle,
                  "--images", "scp://somehost/some-base-cluster-01.gz",
                 ]
    parser = wc_optparse.parsersetup()
    (opts, args) = parser.parse_args(createargs)
    
    p,c = get_pc(opts, realconfigs())
    c.log.debug("test_real_procurement_unpropagate1()")
    
    procure_cls = c.get_class_by_keyword("ImageProcurement")
    procure = procure_cls(p, c)
    procure.validate()
    assert procure.lengthy_shutdown()
    
def test_real_procurement_unpropagate2():
    """Test the procurement adapter unpropagate syntax (negative)"""
    
    handle = "wrksp-414"
    createargs = ["--action", "unpropagate", 
                  "--name", handle,
                  "--images", "file://somehost/some-base-cluster-01.gz",
                 ]
    parser = wc_optparse.parsersetup()
    (opts, args) = parser.parse_args(createargs)
    
    p,c = get_pc(opts, realconfigs())
    c.log.debug("test_real_procurement_unpropagate2()")
    
    procure_cls = c.get_class_by_keyword("ImageProcurement")
    procure = procure_cls(p, c)
    procure.validate()
    
    invalid_input = False
    try:
        procure.lengthy_shutdown()
    except InvalidInput:
        invalid_input = True
    assert invalid_input

def test_real_procurement_unpropagate3():
    """Test that procurement adapter rejects blanksspace requests in unpropagate"""
    
    handle = "wrksp-414"
    createargs = ["--action", "unpropagate", 
                  "--name", handle,
                  "--images", "scp://somehost/some-base-cluster-01.gz;;blankspace://blah-size-40",
                 ]
    parser = wc_optparse.parsersetup()
    (opts, args) = parser.parse_args(createargs)
    
    p,c = get_pc(opts, realconfigs())
    c.log.debug("test_real_procurement_unpropagate2()")
    
    procure_cls = c.get_class_by_keyword("ImageProcurement")
    procure = procure_cls(p, c)
    procure.validate()
    
    invalid_input = False
    try:
        procure.lengthy_shutdown()
    except InvalidInput:
        invalid_input = True
    assert invalid_input
    

def test_notification():
    """Test notification validation (negative1)"""
    
    createargs = ["--action", "unpropagate", 
                  "--name", "wrksp-114",
                  "--images", "scp://somehost/some-base-cluster-01.gz",
                  "--notify", "asd",
                 ]
    parser = wc_optparse.parsersetup()
    (opts, args) = parser.parse_args(createargs)
    
    p,c = get_pc(opts, realconfigs())
    c.log.debug("test_notification()")
    
    notify_cls = c.get_class_by_keyword("AsyncNotification")
    notify = notify_cls(p, c)
    
    invalid_input = False
    try:
        notify.validate()
    except InvalidInput:
        invalid_input = True
    assert invalid_input
    
def test_notification2():
    """Test notification validation (negative2)"""
    
    createargs = ["--action", "unpropagate", 
                  "--name", "wrksp-114",
                  "--images", "scp://somehost/some-base-cluster-01.gz",
                  "--notify", "nimbus@somehost:22",
                 ]
    parser = wc_optparse.parsersetup()
    (opts, args) = parser.parse_args(createargs)
    
    p,c = get_pc(opts, realconfigs())
    c.log.debug("test_notification2()")
    
    notify_cls = c.get_class_by_keyword("AsyncNotification")
    notify = notify_cls(p, c)
    
    invalid_input = False
    try:
        notify.validate()
    except InvalidInput:
        invalid_input = True
    assert invalid_input
    
def test_notification3():
    """Test notification validation"""
    
    handle = "wrksp-104"
    createargs = ["--action", "unpropagate", 
                  "--name", handle,
                  "--images", "scp://somehost/some-base-cluster-01.gz",
                  "--notify", "nimbus@somehost:22/somepath",
                 ]
    parser = wc_optparse.parsersetup()
    (opts, args) = parser.parse_args(createargs)
    
    p,c = get_pc(opts, realconfigs())
    c.log.debug("test_notification3()")
    
    notify_cls = c.get_class_by_keyword("AsyncNotification")
    notify = notify_cls(p, c)
    
    # should throw no error
    notify.validate()
    
    # violating interface contract with 'dryrun' argument
    notify.notify(handle, "propagate", 0, None, dryrun=True)
    notify.notify(handle, "propagate", 1, "bad\nbad\nbad", dryrun=True)
    
    programming_error = False
    try:
        notify.notify(handle, "XYZpropagate", 1, "bad\nbad", dryrun=True)
    except ProgrammingError:
        programming_error = True
    assert programming_error

def test_image_editing1():
    """Test for image editing module task awareness"""
    
    handle = "wrksp-911"
    createargs = ["--action", "create", 
                  "--name", handle,
                  "--images", "scp://somehost/some-base-cluster",
                  "--mnttasks",
                  "d69a9bda-399a-4016-aaee;/root/.ssh/authorized_keys;;3abc9086-d74b-46b0-a3e9;/var/nimbus-metadata-server-url",
                 ]
    parser = wc_optparse.parsersetup()
    (opts, args) = parser.parse_args(createargs)
    
    p,c = get_pc(opts, mockconfigs())
    c.log.debug("test_real_image_editing1()")
    
    editing_cls = c.get_class_by_keyword("ImageEditing")
    editing = editing_cls(p, c)
    editing.validate()
    
    procure_cls = c.get_class_by_keyword("ImageProcurement")
    procure = procure_cls(p, c)
    procure.validate()
    local_file_set = procure.obtain()
    
    editing.process_after_procurement(local_file_set, dryrun=True)
    
    # TODO: could actually test for the existence of the task ... the mock
    # procurement adapter is actually making filesystem images.  But we'd first
    # need a tool to mount and check a filesystem.  And sudo would need to be
    # configured.
    
    # clean up
    procure.process_after_destroy(local_file_set)
    
def test_image_decompress1():
    """Test file decompression"""
    
    # fake image procurement chooses the file names
    createargs = ["--action", "create", 
                  "--name", "wrksp-999",
                 ]
    parser = wc_optparse.parsersetup()
    (opts, args) = parser.parse_args(createargs)
    
    p,c = get_pc(opts, mockconfigs())
    c.log.debug("test_image_decompress1()")
    
    procure_cls = c.get_class_by_keyword("ImageProcurement")
    procure = procure_cls(p, c)
    procure.validate()
    local_file_set = procure.obtain()
    
    editing_cls = c.get_class_by_keyword("ImageEditing")
    editing = editing_cls(p, c)
    editing.validate()
    
    # compress each disk
    oldpaths = []
    for lf in local_file_set.flist():
        # test relies on specific impl method we know is there
        oldpaths.append(lf.path)
        lf.path = editing._gzip_file_inplace(lf.path, False)
    
    for i,lf in enumerate(local_file_set.flist()):
        #c.log.debug("old path: %s" % oldpaths[i])
        #c.log.debug("current path: %s" % lf.path)
        assert oldpaths[i] + ".gz" == lf.path
    
    # process incoming images
    editing.process_after_procurement(local_file_set, dryrun=True)
    
    # see if it is now uncompressed
    for i,lf in enumerate(local_file_set.flist()):
        #c.log.debug("old path: %s" % oldpaths[i])
        #c.log.debug("current path: %s" % lf.path)
        assert oldpaths[i] == lf.path
    
    # clean up
    procure.process_after_destroy(local_file_set)
    
def test_image_compress1():
    """Test file compression"""
    
    createargs = ["--action", "unpropagate", 
                  "--name", "wrksp-929",
                  "--images", "scp://somehost/some-base-cluster-01",
                  "--unproptargets", "scp://somehost/some-newfile.gz",
                 ]
    parser = wc_optparse.parsersetup()
    (opts, args) = parser.parse_args(createargs)
    
    p,c = get_pc(opts, realconfigs())
    c.log.debug("test_image_compress1()")
    
    procure_cls = c.get_class_by_keyword("ImageProcurement")
    procure = procure_cls(p, c)
    procure.validate()
    local_file_set = procure.obtain()
    
    editing_cls = c.get_class_by_keyword("ImageEditing")
    editing = editing_cls(p, c)
    editing.validate()
    
    editing.process_after_shutdown(local_file_set, dryrun=True)
    procure.process_after_shutdown(local_file_set, dryrun=True)
    
def test_localnet1():
    """Test local network adapter basics"""
    
    mock_config_name = "localnet1.conf"
    p,c = get_pc(None, mockconfigs(basename=mock_config_name))
    c.log.debug("test_localnet1()")
    localnet_cls = c.get_class_by_keyword("LocalNetworkSetup")
    localnet = localnet_cls(p,c)
    
    # should validate without error
    localnet.validate()
    
    bridge = localnet.ip_to_bridge("192.168.0.13")
    assert bridge == "virbr3"
    
    bridge = localnet.ip_to_bridge("192.168.2.200")
    assert bridge == "virbr5"
    
    # default:
    bridge = localnet.ip_to_bridge("10.10.2.34")
    assert bridge == "virbr1"
    
def test_localnet2():
    """Test local network adapter with no default bridge"""
    
    mock_config_name = "localnet2.conf"
    p,c = get_pc(None, mockconfigs(basename=mock_config_name))
    c.log.debug("test_localnet2()")
    localnet_cls = c.get_class_by_keyword("LocalNetworkSetup")
    localnet = localnet_cls(p,c)
    localnet.validate()
    
    bridge = localnet.ip_to_bridge("192.168.0.13")
    assert bridge == "virbr3"
    
    bridge = localnet.ip_to_bridge("192.168.2.200")
    assert bridge == "virbr5"
    
    # localnet2.conf has no default and this request is not in any range
    incompat_env = False
    try:
        bridge = localnet.ip_to_bridge("10.10.2.34")
    except IncompatibleEnvironment,e:
        c.log.debug("IncompatibleEnvironment - %s" % e.msg)
        incompat_env = True
    assert incompat_env

def test_localnet3():
    """Test local network adapter with only a default bridge"""
    
    mock_config_name = "localnet3.conf"
    p,c = get_pc(None, mockconfigs(basename=mock_config_name))
    c.log.debug("test_localnet3()")
    localnet_cls = c.get_class_by_keyword("LocalNetworkSetup")
    localnet = localnet_cls(p,c)
    localnet.validate()
    
    bridge = localnet.ip_to_bridge("10.10.2.34")
    assert bridge == "virbr1"
    
def test_localnet4():
    """Test local network adapter errors"""
    
    mock_config_name = "localnet4.conf"
    p,c = get_pc(None, mockconfigs(basename=mock_config_name))
    c.log.debug("test_localnet4()")
    localnet_cls = c.get_class_by_keyword("LocalNetworkSetup")
    localnet = localnet_cls(p,c)
    
    # localnet4.conf has no default and no IP mappings at all
    invalid_config = False
    try:
        localnet.validate()
    except InvalidConfig,e:
        c.log.debug("InvalidConfig - %s" % e.msg)
        invalid_config = True
    assert invalid_config
    
def test_localnet5():
    """Test local network adapter, multiple ranges per bridge"""
    
    mock_config_name = "localnet5.conf"
    p,c = get_pc(None, mockconfigs(basename=mock_config_name))
    c.log.debug("test_localnet5()")
    localnet_cls = c.get_class_by_keyword("LocalNetworkSetup")
    localnet = localnet_cls(p,c)
    
    localnet.validate()
    
    bridge = localnet.ip_to_bridge("10.10.2.34")
    assert bridge == "virbr3"
    
    bridge = localnet.ip_to_bridge("192.168.2.1")
    assert bridge == "virbr5"
    
    bridge = localnet.ip_to_bridge("172.16.5.8")
    assert bridge == "virbr4"
    
    bridge = localnet.ip_to_bridge("172.30.30.99")
    assert bridge == "virbr4"
    
    bridge = localnet.ip_to_bridge("192.168.0.18")
    assert bridge == "virbr3"
    
def test_localnet6():
    """Test local network adapter errors, multiple bridges with same IP range"""
    
    mock_config_name = "localnet6.conf"
    p,c = get_pc(None, mockconfigs(basename=mock_config_name))
    c.log.debug("test_localnet6()")
    localnet_cls = c.get_class_by_keyword("LocalNetworkSetup")
    localnet = localnet_cls(p,c)
    
    # localnet6.conf has two bridges with the same IP ranges
    # note that this does not cover an *overlap* just the same ranges.
    # TODO: analyzing overlaps would be better
    invalid_config = False
    try:
        localnet.validate()
    except InvalidConfig,e:
        c.log.debug("InvalidConfig - %s" % e.msg)
        invalid_config = True
    assert invalid_config
    