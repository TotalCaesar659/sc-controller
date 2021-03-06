#!/usr/bin/env python2

"""
Python wrapper for some X-related stuff.
"""

from ctypes import CDLL, POINTER, c_void_p, Structure
from ctypes import c_ulong, c_int, c_uint, c_short, c_ushort, c_ubyte


def _load_lib(*names):
	"""
	Tries multiple alternative names to load .so library.
	"""
	for l in names:
		try:
			return CDLL(l)
		except OSError:
			pass
	raise OSError("Failed to load %s, library not found" % (names[0],))


libXFixes = _load_lib('libXfixes.so', 'libXfixes.so.3')
libX11 = _load_lib('libX11.so', 'libX11.so.6')


# Types
XID = c_ulong
XserverRegion = c_ulong
Display = c_void_p

# Structures
class XRectangle(Structure):
	_fields_ = [
		('x', c_short),
		('y', c_short),
		('width', c_ushort),
		('height', c_ushort),
	]


class XkbStateRec(Structure):
	_fields_ = [
		('group', c_ubyte),
		('locked_group', c_ubyte),
		('base_group', c_ushort),
		('latched_group', c_ushort),
		('mods', c_ubyte),
		('base_mods', c_ubyte),
		('latched_mods', c_ubyte),
		('locked_mods', c_ubyte),
		('compat_state', c_ubyte),
		('grab_mods', c_ubyte),
		('compat_grab_mods', c_ubyte),
		('lookup_mods', c_ubyte),
		('compat_lookup_mods', c_ubyte),
		('ptr_buttons', c_ushort),
	]


# Consants
SHAPE_BOUNDING	= 0
SHAPE_CLIP		= 1
SHAPE_INPUT		= 2

XKBUSECOREKBD	= 0x0100


# Functions
create_region = libXFixes.XFixesCreateRegion
create_region.argtypes = [c_void_p, POINTER(XRectangle), c_int]
create_region.restype = XserverRegion
set_window_shape_region = libXFixes.XFixesSetWindowShapeRegion
set_window_shape_region.argtypes = [c_void_p, XID, c_int, c_int, c_int, XserverRegion]
destroy_region = libXFixes.XFixesDestroyRegion
destroy_region.argtypes = [c_void_p, XserverRegion]

# Wrapped functions
_xkb_get_state = libX11.XkbGetState
_xkb_get_state.argtypes = [c_void_p, c_uint, POINTER(XkbStateRec)]

# Wrappers
def get_xkb_state(dpy):
	rec = XkbStateRec()
	_xkb_get_state(dpy, XKBUSECOREKBD, rec)
	return rec

