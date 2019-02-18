import datetime
import mock
import os

import pytest
from pyVmomi import vim
import winrm

from vcdriver.exceptions import (
    NoObjectFound,
    TooManyObjectsFound,
    SshError,
    DownloadError,
    UploadError,
    WinRmError,
    TimeoutError,
    NotEnoughDiskSpace
)
from vcdriver.vm import (
    VirtualMachine,
    virtual_machines,
    snapshot,
    get_all_virtual_machines,
)
from vcdriver.config import load


@mock.patch('vcdriver.vm.connection')
@mock.patch('vcdriver.vm.get_vcenter_object_by_name')
@mock.patch('vcdriver.vm.vim.vm.CloneSpec')
@mock.patch('vcdriver.vm.vim.vm.RelocateSpec')
@mock.patch('vcdriver.vm.wait_for_vcenter_task')
def test_virtual_machine_create(
        wait_for_vcenter_task,
        relocate_spec,
        clone_spec,
        get_vcenter_object_by_name,
        connection
):
    os.environ['vcdriver_resource_pool'] = 'something'
    os.environ['vcdriver_data_store'] = 'something'
    os.environ['vcdriver_data_store_threshold'] = '20'
    os.environ['vcdriver_folder'] = 'something'
    load()
    vm = VirtualMachine()
    vm.create()
    vm.create()
    assert vm.__getattribute__('_vm_object') is not None
    assert wait_for_vcenter_task.call_count == 1


@mock.patch('vcdriver.vm.connection')
@mock.patch('vcdriver.vm.get_vcenter_object_by_name')
@mock.patch('vcdriver.vm.vim.vm.CloneSpec')
@mock.patch('vcdriver.vm.vim.vm.RelocateSpec')
@mock.patch('vcdriver.vm.wait_for_vcenter_task')
def test_virtual_machine_create_not_enough_disk_space(
        wait_for_vcenter_task,
        relocate_spec,
        clone_spec,
        get_vcenter_object_by_name,
        connection
):
    os.environ['vcdriver_resource_pool'] = 'something'
    os.environ['vcdriver_data_store'] = 'something'
    os.environ['vcdriver_data_store_threshold'] = '120'
    os.environ['vcdriver_folder'] = 'something'
    load()
    vm = VirtualMachine()
    with pytest.raises(NotEnoughDiskSpace):
        vm.create()
    assert vm.__getattribute__('_vm_object') is None
    assert wait_for_vcenter_task.call_count == 0


@mock.patch('vcdriver.vm.connection')
@mock.patch('vcdriver.vm.wait_for_vcenter_task')
def test_virtual_machine_destroy_vm_on(wait_for_vcenter_task, connection):
    vm = VirtualMachine()
    vm_object_mock = mock.MagicMock()
    vm.__setattr__('_vm_object', vm_object_mock)
    vm.destroy()
    vm.destroy()
    assert vm.__getattribute__('_vm_object') is None
    assert wait_for_vcenter_task.call_count == 2


@mock.patch('vcdriver.vm.connection')
@mock.patch('vcdriver.vm.wait_for_vcenter_task')
def test_virtual_machine_destroy_vm_off(wait_for_vcenter_task, connection):
    vm = VirtualMachine()
    vm_object_mock = mock.MagicMock()
    vm.__setattr__('_vm_object', vm_object_mock)
    wait_for_vcenter_task.side_effect = [vim.fault.InvalidPowerState, None]
    vm.destroy()
    vm.destroy()
    assert vm.__getattribute__('_vm_object') is None
    assert wait_for_vcenter_task.call_count == 2


@mock.patch('vcdriver.vm.connection')
@mock.patch('vcdriver.vm.get_vcenter_object_by_name')
def test_virtual_machine_find(get_vcenter_object_by_name, connection):
    vm = VirtualMachine()
    vm.find()
    vm.find()
    assert vm.__getattribute__('_vm_object') is not None
    assert get_vcenter_object_by_name.call_count == 1


@mock.patch('vcdriver.vm.connection')
@mock.patch('vcdriver.vm.get_vcenter_object_by_name')
@mock.patch('vcdriver.vm.close')
def test_virtual_machine_refresh(close, get_vcenter_object_by_name, connection):
    vm = VirtualMachine()
    assert vm.__getattribute__('_vm_object') is None

    # Test that refresh does nothing if no _vm_object
    vm.refresh()
    assert vm.__getattribute__('_vm_object') is None

    # Test that refresh assigns a new _vm_object
    vm.__setattr__('_vm_object', mock.Mock())

    initial__vm_object = vm.__getattribute__('_vm_object')
    assert initial__vm_object is not None
    vm.refresh()

    refreshed__vm_object = vm.__getattribute__('_vm_object')
    assert refreshed__vm_object is not None

    assert initial__vm_object != refreshed__vm_object

    close.assert_called_once()
    get_vcenter_object_by_name.assert_called_once()


@mock.patch('vcdriver.vm.connection')
def test_virtual_machine_reboot(connection):
    vm = VirtualMachine()
    vm_object_mock = mock.MagicMock()
    reboot_mock = mock.MagicMock()
    vm_object_mock.RebootGuest = reboot_mock
    vm_object_mock.summary.runtime.powerState = 'poweredOn'
    vm_object_mock.summary.guest.toolsRunningStatus = 'guestToolsRunning'
    vm.reboot()
    vm.__setattr__('_vm_object', vm_object_mock)
    vm.reboot()
    assert reboot_mock.call_count == 1


@mock.patch('vcdriver.vm.connection')
def test_virtual_machine_reboot_wrong_power_state(connection):
    vm = VirtualMachine()
    vm_object_mock = mock.MagicMock()
    reboot_mock = mock.MagicMock()
    vm_object_mock.summary.runtime.powerState = 'poweredOff'
    vm_object_mock.summary.guest.toolsRunningStatus = 'guestToolsRunning'
    vm_object_mock.RebootGuest = reboot_mock
    vm.reboot()
    vm.__setattr__('_vm_object', vm_object_mock)
    vm.reboot()
    assert reboot_mock.call_count == 0


@mock.patch('vcdriver.vm.connection')
def test_virtual_machine_shutdown(connection):
    vm = VirtualMachine()
    vm_object_mock = mock.MagicMock()
    shutdown_mock = mock.MagicMock()
    vm_object_mock.ShutdownGuest = shutdown_mock
    vm_object_mock.summary.runtime.powerState = 'poweredOn'
    vm_object_mock.summary.guest.toolsRunningStatus = 'guestToolsRunning'
    vm.shutdown()
    vm.__setattr__('_vm_object', vm_object_mock)
    vm.shutdown()
    assert shutdown_mock.call_count == 1


@mock.patch('vcdriver.vm.connection')
def test_virtual_machine_shutdown_wrong_power_state(connection):
    vm = VirtualMachine()
    vm_object_mock = mock.MagicMock()
    shutdown_mock = mock.MagicMock()
    vm_object_mock.ShutdownGuest = shutdown_mock
    vm_object_mock.summary.runtime.powerState = 'poweredOff'
    vm_object_mock.summary.guest.toolsRunningStatus = 'guestToolsRunning'
    vm.shutdown()
    vm.__setattr__('_vm_object', vm_object_mock)
    vm.shutdown()
    assert shutdown_mock.call_count == 0


@mock.patch('vcdriver.vm.connection')
@mock.patch('vcdriver.vm.wait_for_vcenter_task')
def test_virtual_machine_power_on(wait_for_vcenter_task, connection):
    vm = VirtualMachine()
    vm.power_on()
    vm.__setattr__('_vm_object', mock.MagicMock())
    vm.power_on()
    assert wait_for_vcenter_task.call_count == 1


@mock.patch('vcdriver.vm.connection')
@mock.patch('vcdriver.vm.wait_for_vcenter_task')
def test_virtual_machine_power_on_wrong_power_state(
        wait_for_vcenter_task, connection
):
    wait_for_vcenter_task.side_effect = vim.fault.InvalidPowerState
    vm = VirtualMachine()
    vm.power_on()
    vm.__setattr__('_vm_object', mock.MagicMock())
    vm.power_on()
    assert wait_for_vcenter_task.call_count == 1


@mock.patch('vcdriver.vm.connection')
@mock.patch('vcdriver.vm.wait_for_vcenter_task')
def test_virtual_machine_power_off(wait_for_vcenter_task, connection):
    vm = VirtualMachine()
    vm.power_off()
    vm.__setattr__('_vm_object', mock.MagicMock())
    vm.power_off()
    assert wait_for_vcenter_task.call_count == 1


@mock.patch('vcdriver.vm.connection')
@mock.patch('vcdriver.vm.wait_for_vcenter_task')
def test_virtual_machine_reset(wait_for_vcenter_task, connection):
    vm = VirtualMachine()
    vm.reset()
    vm.__setattr__('_vm_object', mock.MagicMock())
    vm.reset()
    assert wait_for_vcenter_task.call_count == 1


@mock.patch('vcdriver.vm.connection')
@mock.patch('vcdriver.vm.wait_for_vcenter_task')
def test_virtual_machine_reset_wrong_power_state(
        wait_for_vcenter_task, connection
):
    wait_for_vcenter_task.side_effect = vim.fault.InvalidPowerState
    vm = VirtualMachine()
    vm.reset()
    vm.__setattr__('_vm_object', mock.MagicMock())
    vm.reset()
    assert wait_for_vcenter_task.call_count == 1


@mock.patch('vcdriver.vm.connection')
def test_virtual_machine_ip(connection):
    vm = VirtualMachine()
    vm_object_mock = mock.MagicMock()
    vm_object_mock.summary.guest.ipAddress = '127.0.0.1'
    assert vm.ip() is None
    vm.__setattr__('_vm_object', vm_object_mock)
    assert vm.ip() == '127.0.0.1'
    assert vm.ip() == '127.0.0.1'


@mock.patch('vcdriver.vm.connection')
@mock.patch('vcdriver.vm.timeout_loop')
@mock.patch('vcdriver.vm.validate_ip')
def test_virtual_machine_ip_with_dhcp_wait(
        validate_ip, timeout_loop, connection
):
    vm = VirtualMachine()
    validate_ip.side_effect = lambda x: x
    vm_object_mock = mock.MagicMock()
    vm_object_mock.summary.guest.ipAddress = None
    vm.__setattr__('_vm_object', vm_object_mock)
    assert vm.ip() is None


@mock.patch('vcdriver.vm.connection')
def test_virtual_machine_ip_timeout(connection):
    vm = VirtualMachine(timeout=1)
    vm_object_mock = mock.MagicMock()
    vm_object_mock.summary.guest.ipAddress = None
    vm.__setattr__('_vm_object', vm_object_mock)
    with pytest.raises(TimeoutError):
        vm.ip()


@mock.patch('vcdriver.vm.connection')
@mock.patch('vcdriver.vm.sudo')
@mock.patch('vcdriver.vm.run')
@mock.patch('vcdriver.helpers.run')
def test_virtual_machine_ssh_success(helpers_run, vm_run, sudo, connection):
    os.environ['vcdriver_vm_ssh_username'] = 'user'
    os.environ['vcdriver_vm_ssh_password'] = 'pass'
    load()
    vm = VirtualMachine()
    assert vm.ssh('whatever') is None
    vm_object_mock = mock.MagicMock()
    vm_object_mock.summary.guest.ipAddress = '127.0.0.1'
    vm.__setattr__('_vm_object', vm_object_mock)
    result_mock = mock.MagicMock()
    result_mock.return_code = 3
    result_mock.failed = False
    helpers_run.return_value = result_mock
    vm_run.return_value = result_mock
    sudo.return_value = result_mock
    assert vm.ssh('whatever', use_sudo=False).return_code == 3
    assert vm.ssh('whatever', use_sudo=True).return_code == 3
    assert vm.ssh('whatever', quiet=True).return_code == 3


@mock.patch('vcdriver.vm.connection')
@mock.patch('vcdriver.vm.sudo')
@mock.patch('vcdriver.vm.run')
@mock.patch('vcdriver.helpers.run')
def test_virtual_machine_ssh_fail(sudo, helpers_run, vm_run, connection):
    os.environ['vcdriver_vm_ssh_username'] = 'user'
    os.environ['vcdriver_vm_ssh_password'] = 'pass'
    load()
    vm = VirtualMachine()
    vm_object_mock = mock.MagicMock()
    vm_object_mock.summary.guest.ipAddress = 'fe80::250:56ff:febf:1a0a'
    vm.__setattr__('_vm_object', vm_object_mock)
    with pytest.raises(SshError):
        vm.ssh('whatever', use_sudo=True)


@mock.patch('vcdriver.vm.connection')
@mock.patch('vcdriver.vm.run')
@mock.patch('vcdriver.helpers.run')
def test_virtual_machine_ssh_timeout(helpers_run, vm_run, connection):
    os.environ['vcdriver_vm_ssh_username'] = 'user'
    os.environ['vcdriver_vm_ssh_password'] = 'pass'
    load()
    vm = VirtualMachine(timeout=1)
    vm_object_mock = mock.MagicMock()
    vm_object_mock.summary.guest.ipAddress = '127.0.0.1'
    vm.__setattr__('_vm_object', vm_object_mock)
    helpers_run.side_effect = Exception
    vm_run.side_effect = Exception
    with pytest.raises(TimeoutError):
        vm.ssh('whatever', use_sudo=True)


@mock.patch('vcdriver.vm.connection')
@mock.patch('vcdriver.vm.put')
@mock.patch('vcdriver.vm.run')
@mock.patch('vcdriver.helpers.run')
def test_virtual_machine_ssh_upload_success(
        helpers_run, vm_run, put, connection
):
    os.environ['vcdriver_vm_ssh_username'] = 'user'
    os.environ['vcdriver_vm_ssh_password'] = 'pass'
    load()
    vm = VirtualMachine()
    assert vm.ssh_upload('from', 'to') is None
    vm_object_mock = mock.MagicMock()
    vm_object_mock.summary.guest.ipAddress = '127.0.0.1'
    vm.__setattr__('_vm_object', vm_object_mock)
    result_mock = mock.MagicMock()
    result_mock.failed = False
    put.return_value = result_mock
    assert vm.ssh_upload('from', 'to') == result_mock
    assert vm.ssh_upload('from', 'to', quiet=True) == result_mock


@mock.patch('vcdriver.vm.connection')
@mock.patch('vcdriver.vm.put')
@mock.patch('vcdriver.vm.run')
@mock.patch('vcdriver.helpers.run')
def test_virtual_machine_ssh_upload_fail(helpers_run, vm_run, put, connection):
    os.environ['vcdriver_vm_ssh_username'] = 'user'
    os.environ['vcdriver_vm_ssh_password'] = 'pass'
    load()
    vm = VirtualMachine()
    vm_object_mock = mock.MagicMock()
    vm_object_mock.summary.guest.ipAddress = '127.0.0.1'
    vm.__setattr__('_vm_object', vm_object_mock)
    with pytest.raises(UploadError):
        vm.ssh_upload('from', 'to')


@mock.patch('vcdriver.vm.connection')
@mock.patch('vcdriver.vm.get')
@mock.patch('vcdriver.vm.run')
@mock.patch('vcdriver.helpers.run')
def test_virtual_machine_ssh_download_success(
        helpers_run, vm_run, get, session
):
    os.environ['vcdriver_vm_ssh_username'] = 'user'
    os.environ['vcdriver_vm_ssh_password'] = 'pass'
    load()
    vm = VirtualMachine()
    assert vm.ssh_download('from', 'to') is None
    vm_object_mock = mock.MagicMock()
    vm_object_mock.summary.guest.ipAddress = '127.0.0.1'
    vm.__setattr__('_vm_object', vm_object_mock)
    result_mock = mock.MagicMock()
    result_mock.failed = False
    get.return_value = result_mock
    assert vm.ssh_download('from', 'to') == result_mock
    assert vm.ssh_download('from', 'to', quiet=True) == result_mock


@mock.patch('vcdriver.vm.connection')
@mock.patch('vcdriver.vm.get')
@mock.patch('vcdriver.vm.run')
@mock.patch('vcdriver.helpers.run')
def test_virtual_machine_ssh_download_fail(helpers_run, vm_run, get, session):
    os.environ['vcdriver_vm_ssh_username'] = 'user'
    os.environ['vcdriver_vm_ssh_password'] = 'pass'
    load()
    vm = VirtualMachine()
    vm_object_mock = mock.MagicMock()
    vm_object_mock.summary.guest.ipAddress = '127.0.0.1'
    vm.__setattr__('_vm_object', vm_object_mock)
    with pytest.raises(DownloadError):
        vm.ssh_download('from', 'to')


@mock.patch('vcdriver.vm.connection')
@mock.patch.object(winrm.Session, 'run_ps')
def test_virtual_machine_winrm_success(run_ps, connection):
    os.environ['vcdriver_vm_winrm_username'] = 'user'
    os.environ['vcdriver_vm_winrm_password'] = 'pass'
    load()
    vm = VirtualMachine()
    assert vm.winrm('whatever', dict()) is None
    vm_object_mock = mock.MagicMock()
    vm_object_mock.summary.guest.ipAddress = '127.0.0.1'
    vm.__setattr__('_vm_object', vm_object_mock)
    run_ps.return_value.status_code = 0
    vm.winrm('script', dict())
    vm.winrm('script', dict(), quiet=True)
    run_ps.assert_called_with('script')
    assert run_ps.call_count == 4


@mock.patch('vcdriver.vm.connection')
@mock.patch.object(winrm.Session, 'run_ps')
def test_virtual_machine_winrm_fail(run_ps, connection):
    os.environ['vcdriver_vm_winrm_username'] = 'user'
    os.environ['vcdriver_vm_winrm_password'] = 'pass'
    load()
    vm = VirtualMachine()
    vm_object_mock = mock.MagicMock()
    vm_object_mock.summary.guest.ipAddress = '127.0.0.1'
    vm.__setattr__('_vm_object', vm_object_mock)
    run_ps.return_value.status_code = 1
    with pytest.raises(WinRmError):
        vm.winrm('script', dict())
    with pytest.raises(WinRmError):
        vm.winrm('script', dict(), quiet=True)


@mock.patch('vcdriver.vm.connection')
@mock.patch.object(winrm.Session, 'run_ps')
def test_virtual_machine_winrm_timeout(run_ps, connection):
    os.environ['vcdriver_vm_winrm_username'] = 'user'
    os.environ['vcdriver_vm_winrm_password'] = 'pass'
    load()
    vm = VirtualMachine(timeout=1)
    vm_object_mock = mock.MagicMock()
    vm_object_mock.summary.guest.ipAddress = '127.0.0.1'
    vm.__setattr__('_vm_object', vm_object_mock)
    run_ps.side_effect = Exception
    with pytest.raises(TimeoutError):
        vm.winrm('script', dict())


@mock.patch('vcdriver.vm.os.stat')
@mock.patch('vcdriver.vm.open')
@mock.patch('vcdriver.vm.connection')
@mock.patch.object(winrm.Session, 'run_ps')
def test_virtual_machine_winrm_upload_success(
        run_ps, connection, open, os_stat
):
    st_size_mock = mock.Mock()
    st_size_mock.st_size = 3
    os_stat.return_value = st_size_mock
    code_mock = mock.Mock()
    code_mock.status_code = 0
    run_ps.return_value = code_mock
    read_mock = mock.Mock
    read_mock.read = lambda x, y: b'\0\0\0'
    open.__enter__ = read_mock
    open.__exit__ = mock.Mock()
    os.environ['vcdriver_vm_winrm_username'] = 'user'
    os.environ['vcdriver_vm_winrm_password'] = 'pass'
    load()
    vm = VirtualMachine()
    assert vm.winrm_upload('whatever', 'whatever') is None
    vm_object_mock = mock.MagicMock()
    vm_object_mock.summary.guest.ipAddress = '127.0.0.1'
    vm.__setattr__('_vm_object', vm_object_mock)
    assert vm.winrm_upload('whatever', 'whatever', step=2) is None
    assert vm.winrm_upload('whatever', 'whatever', step=2, quiet=True) is None


@mock.patch('vcdriver.vm.os.stat')
@mock.patch('vcdriver.vm.open')
@mock.patch('vcdriver.vm.connection')
@mock.patch.object(winrm.Session, 'run_ps')
def test_virtual_machine_winrm_upload_fail(run_ps, connection, open, os_stat):
    st_size_mock = mock.Mock()
    st_size_mock.st_size = 3
    os_stat.return_value = st_size_mock
    code_mock = mock.Mock()
    code_mock.status_code = 1
    code_mock.std_err = 'Whatever'.encode('ascii')
    run_ps.return_value = code_mock
    read_mock = mock.Mock
    read_mock.read = lambda x, y: b'\0\0\0'
    open.__enter__ = read_mock
    open.__exit__ = mock.Mock()
    os.environ['vcdriver_vm_winrm_username'] = 'user'
    os.environ['vcdriver_vm_winrm_password'] = 'pass'
    load()
    vm = VirtualMachine()
    vm_object_mock = mock.MagicMock()
    vm_object_mock.summary.guest.ipAddress = '127.0.0.1'
    vm.__setattr__('_vm_object', vm_object_mock)
    with pytest.raises(WinRmError):
        vm.winrm_upload('whatever', 'whatever', step=2)


@mock.patch('vcdriver.vm.os.stat')
@mock.patch('vcdriver.vm.open')
@mock.patch('vcdriver.vm.connection')
@mock.patch.object(winrm.Session, 'run_ps')
def test_virtual_machine_winrm_upload_timeout(
        run_ps, connection, open, os_stat
):
    st_size_mock = mock.Mock()
    st_size_mock.st_size = 3
    os_stat.return_value = st_size_mock
    code_mock = mock.Mock()
    code_mock.status_code = 1
    code_mock.std_err = 'Blah is being used by another process'.encode('ascii')
    run_ps.return_value = code_mock
    read_mock = mock.Mock
    read_mock.read = lambda x, y: b'\0\0\0'
    open.__enter__ = read_mock
    open.__exit__ = mock.Mock()
    os.environ['vcdriver_vm_winrm_username'] = 'user'
    os.environ['vcdriver_vm_winrm_password'] = 'pass'
    load()
    vm = VirtualMachine()
    vm_object_mock = mock.MagicMock()
    vm_object_mock.summary.guest.ipAddress = '127.0.0.1'
    vm.__setattr__('_vm_object', vm_object_mock)
    vm.timeout = 1
    with pytest.raises(TimeoutError):
        vm.winrm_upload('whatever', 'whatever', step=2)


@mock.patch('vcdriver.vm.wait_for_vcenter_task')
def test_virtual_machine_find_snapshot(wait_for_vcenter_task):
    fake_snapshots = [mock.MagicMock(), mock.MagicMock(), mock.MagicMock()]
    for fake_snapshot in fake_snapshots[:-1]:
        fake_snapshot.name = 'snapshot'
        fake_snapshot.childSnapshotList = []
    fake_snapshots[-1].name = 'other'
    fake_snapshots[-1].childSnapshotList = []
    vm = VirtualMachine()
    assert vm.find_snapshot('snapshot') is None
    vm_object_mock = mock.MagicMock()
    vm.__setattr__('_vm_object', vm_object_mock)
    vm_object_mock.snapshot.rootSnapshotList = []
    with pytest.raises(NoObjectFound):
        vm.find_snapshot('snapshot')
    vm_object_mock.snapshot.rootSnapshotList = fake_snapshots[:-2]
    vm.find_snapshot('snapshot')
    vm_object_mock.snapshot.rootSnapshotList = fake_snapshots
    with pytest.raises(TooManyObjectsFound):
        vm.find_snapshot('snapshot')
    vm_object_mock.snapshot = None
    with pytest.raises(NoObjectFound):
        vm.find_snapshot('snapshot')


@mock.patch('vcdriver.vm.wait_for_vcenter_task')
def test_virtual_machine_create_snapshot(wait_for_vcenter_task):
    fake_snapshot = mock.MagicMock()
    fake_snapshot.name = 'snapshot'
    fake_snapshot.childSnapshotList = []
    vm = VirtualMachine()
    assert vm.create_snapshot('snapshot', True) is None
    vm_object_mock = mock.MagicMock()
    vm_object_mock.snapshot.rootSnapshotList = []
    vm.__setattr__('_vm_object', vm_object_mock)
    vm.create_snapshot('snapshot', True)
    vm_object_mock.snapshot.rootSnapshotList = [fake_snapshot]
    with pytest.raises(TooManyObjectsFound):
        vm.create_snapshot('snapshot', True)


@mock.patch('vcdriver.vm.wait_for_vcenter_task')
def test_virtual_machine_revert_snapshot(wait_for_vcenter_task):
    vm = VirtualMachine()
    assert vm.revert_snapshot('snapshot') is None
    vm.find_snapshot = mock.MagicMock()
    vm.__setattr__('_vm_object', mock.MagicMock())
    vm.revert_snapshot('snapshot')


@mock.patch('vcdriver.vm.wait_for_vcenter_task')
def test_virtual_machine_remove_snapshot(wait_for_vcenter_task):
    vm = VirtualMachine()
    assert vm.remove_snapshot('snapshot') is None
    vm.find_snapshot = mock.MagicMock()
    vm.__setattr__('_vm_object', mock.MagicMock())
    vm.remove_snapshot('snapshot')


@mock.patch('vcdriver.vm.vim.host.AutoStartManager.AutoPowerInfo')
def test_set_autostart(init):
    vm = VirtualMachine()
    vm.set_autostart()
    vm.__setattr__('_vm_object', mock.MagicMock())
    vm.set_autostart()


@mock.patch('vcdriver.vm.connection')
def test_virtual_machine_summary(connection):
    print(VirtualMachine().summary())


def test_str_repr():
    assert str(VirtualMachine(name='whatever')) == 'whatever'
    assert repr(VirtualMachine(name='whatever')) == 'whatever'


@mock.patch('vcdriver.vm.connection')
@mock.patch.object(VirtualMachine, 'create')
@mock.patch.object(VirtualMachine, 'destroy')
def test_virtual_machines_success(destroy, create, connection):
    vm = VirtualMachine()
    with virtual_machines([vm]):
        pass
    create.assert_called_once_with()
    destroy.assert_called_once_with()


@mock.patch('vcdriver.vm.connection')
@mock.patch.object(VirtualMachine, 'create')
@mock.patch.object(VirtualMachine, 'destroy')
def test_virtual_machines_fail(destroy, create, connection):
    vm = VirtualMachine()
    with pytest.raises(Exception):
        with virtual_machines([vm]):
            raise Exception
    create.assert_called_once_with()
    destroy.assert_called_once_with()


@mock.patch.object(VirtualMachine, 'create_snapshot')
@mock.patch.object(VirtualMachine, 'revert_snapshot')
@mock.patch.object(VirtualMachine, 'remove_snapshot')
def test_snapshot_success(remove, revert, create):
    vm = VirtualMachine()
    with snapshot(vm):
        pass
    create.assert_called_once()
    revert.assert_called_once()
    remove.assert_called_once()


@mock.patch.object(VirtualMachine, 'create_snapshot')
@mock.patch.object(VirtualMachine, 'revert_snapshot')
@mock.patch.object(VirtualMachine, 'remove_snapshot')
def test_snapshot_fail(remove, revert, create):
    vm = VirtualMachine()
    with pytest.raises(Exception):
        with snapshot(vm):
            raise Exception
    create.assert_called_once()
    revert.assert_called_once()
    remove.assert_called_once()


@mock.patch('vcdriver.vm.connection')
@mock.patch('vcdriver.vm.get_all_vcenter_objects')
def test_get_all_virtual_machines(get_all_vcenter_objects, connection):
    obj1 = mock.MagicMock()
    obj2 = mock.MagicMock()
    get_all_vcenter_objects.return_value = [obj1, obj2]
    assert len(get_all_virtual_machines()) == 2


@mock.patch('vcdriver.vm.connection')
def test_created_at(connection):
    vm = VirtualMachine()
    vm_object_mock = mock.MagicMock()
    vm_object_mock.config.changeVersion = '2018-06-13T15:12:43.700814Z'
    vm.__setattr__('_vm_object', vm_object_mock)
    assert vm.created_at == datetime.datetime(2018, 6, 13, 15, 12, 43, 700814)
