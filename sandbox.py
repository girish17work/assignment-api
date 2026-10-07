"""Linux defense in depth for a small assignment service, not a security guarantee."""
import ctypes
import ctypes.util
import errno
import os
import resource


class ScmpArgCmp(ctypes.Structure):
    _fields_ = [("arg", ctypes.c_uint), ("op", ctypes.c_int),
                ("datum_a", ctypes.c_uint64), ("datum_b", ctypes.c_uint64)]


def restrict_worker():
    resource.setrlimit(resource.RLIMIT_AS, (128 * 1024 * 1024,) * 2)
    resource.setrlimit(resource.RLIMIT_CPU, (3, 3))
    resource.setrlimit(resource.RLIMIT_FSIZE, (0, 0))
    resource.setrlimit(resource.RLIMIT_CORE, (0, 0))
    resource.setrlimit(resource.RLIMIT_NOFILE, (32, 32))
    libc = ctypes.CDLL(None, use_errno=True)
    if libc.prctl(38, 1, 0, 0, 0):
        raise RuntimeError("Cannot enable no_new_privs")
    lib = ctypes.CDLL(ctypes.util.find_library("seccomp") or "libseccomp.so.2")
    lib.seccomp_init.argtypes = [ctypes.c_uint32]
    lib.seccomp_init.restype = ctypes.c_void_p
    lib.seccomp_syscall_resolve_name.argtypes = [ctypes.c_char_p]
    lib.seccomp_syscall_resolve_name.restype = ctypes.c_int
    lib.seccomp_rule_add_array.argtypes = [ctypes.c_void_p, ctypes.c_uint32,
                                         ctypes.c_int, ctypes.c_uint, ctypes.POINTER(ScmpArgCmp)]
    lib.seccomp_load.argtypes = [ctypes.c_void_p]
    lib.seccomp_release.argtypes = [ctypes.c_void_p]
    ctx = lib.seccomp_init(0x7FFF0000)  # SCMP_ACT_ALLOW
    if not ctx:
        raise RuntimeError("Cannot create syscall filter")
    denied = 0x00050000 | errno.EPERM

    def deny(name, comparison=None):
        syscall = lib.seccomp_syscall_resolve_name(name.encode())
        if syscall < 0:
            return
        count = 1 if comparison is not None else 0
        pointer = ctypes.pointer(comparison) if comparison is not None else None
        if lib.seccomp_rule_add_array(ctx, denied, syscall, count, pointer):
            raise RuntimeError("Cannot install syscall rule")

    try:
        for name in (
            "socket", "socketpair", "connect", "bind", "listen", "accept", "accept4",
            "fork", "vfork", "clone", "clone3", "execve", "execveat", "ptrace",
            "process_vm_readv", "process_vm_writev", "kill", "tkill", "tgkill",
            "mount", "umount2", "unshare", "setns", "bpf", "io_uring_setup",
            "chmod", "fchmod", "fchmodat", "chown", "fchown", "fchownat",
            "unlink", "unlinkat", "rename", "renameat", "renameat2", "mkdir", "mkdirat",
            "rmdir", "link", "linkat", "symlink", "symlinkat", "creat", "truncate",
            "ftruncate", "openat2", "mknod", "mknodat",
        ):
            deny(name)
        for name, arg in (("open", 1), ("openat", 2)):
            for flag in (os.O_WRONLY, os.O_RDWR, os.O_CREAT, os.O_TRUNC, os.O_APPEND):
                deny(name, ScmpArgCmp(arg, 7, flag, flag))  # SCMP_CMP_MASKED_EQ
        if lib.seccomp_load(ctx):
            raise RuntimeError("Cannot activate syscall filter")
    finally:
        lib.seccomp_release(ctx)
