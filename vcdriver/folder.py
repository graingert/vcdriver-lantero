from pyVmomi import vim

from vcdriver.auth import Session
from vcdriver.helpers import get_vcenter_object
from vcdriver.vm import VirtualMachine


def destroy_virtual_machines(folder_name):
    """
    Destroy all the virtual machines in the folder with the given name
    :param folder_name: The folder name
    """
    folder = get_vcenter_object(Session().connection, vim.Folder, folder_name)
    destroyed_vms = []
    for entity in folder.childEntity:
        if isinstance(entity, vim.VirtualMachine):
            vm = VirtualMachine(name=entity.summary.config.name)
            vm.__setattr__('_vm_object', entity)
            vm.destroy()
            destroyed_vms.append(vm)
    return destroyed_vms