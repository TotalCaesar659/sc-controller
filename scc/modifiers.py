#!/usr/bin/env python2
"""
SC Controller - Modifiers

Modifier is Action that just sits between input and actual action, changing
way how resulting action works.
For example, click() modifier executes action only if pad is pressed.
"""
from __future__ import unicode_literals

from scc.actions import Action, NoAction, ACTIONS
from scc.constants import LEFT, RIGHT, STICK, SCButtons, HapticPos
from scc.constants import FE_STICK, FE_TRIGGER, FE_PAD
from scc.controller import HapticData

import time, logging
log = logging.getLogger("Modifiers")
_ = lambda x : x

class Modifier(Action):
	def __init__(self, action=None):
		Action.__init__(self, action)
		self.action = action or NoAction()
	
	def __str__(self):
		return "<Modifier '%s', %s>" % (self.COMMAND, self.action)
	
	def set_haptic(self, hapticdata):
		return self.action.set_haptic(hapticdata)
	
	def set_speed(self, x, y, z):
		return self.action.set_speed(x, y, z)
	
	def encode(self):
		rv = self.action.encode()
		if self.name: rv['name'] = self.name
		return rv
		
	__repr__ = __str__


class ClickModifier(Modifier):
	COMMAND = "click"
	
	def describe(self, context):
		if context in (Action.AC_STICK, Action.AC_PAD):
			return _("(if pressed)") + "\n" + self.action.describe(context)
		else:
			return _("(if pressed)") + " " + self.action.describe(context)
	
	
	def to_string(self, multiline=False, pad=0):
		if multiline:
			childstr = self.action.to_string(True, pad + 2)
			if "\n" in childstr:
				return ((" " * pad) + "click(\n" +
					childstr + "\n" + (" " * pad) + ")")
		return "click( " + self.action.to_string() + " )"
	
	
	def strip(self):
		return self.action.strip()
	
	
	def encode(self):
		rv = Modifier.encode(self)
		rv['click'] = True
		return rv
	
	
	def compress(self):
		self.action = self.action.compress()
		return self
	
	
	# For button press & co it's safe to assume that they are being pressed...
	def button_press(self, mapper):
		return self.action.button_press(mapper)
	
	def button_release(self, mapper):
		return self.action.button_release(mapper)
	
	def trigger(self, mapper, position, old_position):
		return self.action.trigger(mapper, position, old_position)
	
	
	def axis(self, mapper, position, what):
		if what in (STICK, LEFT) and mapper.is_pressed(SCButtons.LPAD):
			if what == STICK: mapper.force_event.add(FE_STICK)
			return self.action.axis(mapper, position, what)
		if what in (STICK, LEFT) and mapper.was_pressed(SCButtons.LPAD):
			# Just released
			return self.action.axis(mapper, 0, what)
		# what == RIGHT, there are only three options
		if mapper.is_pressed(SCButtons.RPAD):
			return self.action.axis(mapper, position, what)
		if mapper.was_pressed(SCButtons.RPAD):
			# Just released
			return self.action.axis(mapper, 0, what)
	
	
	def pad(self, mapper, position, what):
		if what == LEFT and mapper.is_pressed(SCButtons.LPAD):
			if what == STICK: mapper.force_event.add(FE_STICK)
			return self.action.pad(mapper, position, what)
		if what == LEFT and mapper.was_pressed(SCButtons.LPAD):
			# Just released
			return self.action.pad(mapper, 0, what)
		# what == RIGHT, there are only two options
		if mapper.is_pressed(SCButtons.RPAD):
			return self.action.pad(mapper, position, what)
		if mapper.was_pressed(SCButtons.RPAD):
			# Just released
			return self.action.pad(mapper, 0, what)
	
	
	def whole(self, mapper, x, y, what):
		if what in (STICK, LEFT) and mapper.is_pressed(SCButtons.LPAD):
			if what == STICK: mapper.force_event.add(FE_STICK)
			return self.action.whole(mapper, x, y, what)
		if what in (STICK, LEFT) and mapper.was_pressed(SCButtons.LPAD):
			# Just released
			return self.action.whole(mapper, 0, 0, what)
		# what == RIGHT, there are only three options
		if mapper.is_pressed(SCButtons.RPAD):
			# mapper.force_event.add(FE_PAD)
			return self.action.whole(mapper, x, y, what)
		if mapper.was_pressed(SCButtons.RPAD):
			# Just released
			return self.action.whole(mapper, 0, 0, what)


class ModeModifier(Modifier):
	COMMAND = "mode"
	MIN_TRIGGER = 2		# When trigger is bellow this position, list of held_triggers is cleared
	MIN_STICK = 2		# When abs(stick) < MIN_STICK, stick is considered released and held_sticks is cleared
	
	def __init__(self, *stuff):
		Modifier.__init__(self)
		self.default = None
		self.mods = {}
		self.held_buttons = set()
		self.held_sticks = set()
		self.held_triggers = {}
		self.order = []
		self.old_gyro = None
		button = None
		for i in stuff:
			if self.default is not None:
				# Default has to be last parameter
				raise ValueError("Invalid parameters for 'mode'")
			if isinstance(i, Action):
				if button is None:
					self.default = i
					continue
				self.mods[button] = i
				self.order.append(button)
				button = None
			elif i in SCButtons:
				button = i
			else:
				raise ValueError("Invalid parameter for 'mode': %s" % (i,))
		if self.default is None:
			self.default = NoAction()
	
	
	def set_haptic(self, hapticdata):
		supports = False
		if self.default:
			supports = self.default.set_haptic(hapticdata) or supports
		for a in self.mods.values():
			supports = a.set_haptic(hapticdata) or supports
		return supports
	
	
	def set_speed(self, x, y, z):
		supports = False
		if self.default:
			supports = self.default.set_speed(x, y, z) or supports
		for a in self.mods.values():
			supports = a.set_speed(x, y, z) or supports
		return supports
	
	
	def strip(self):
		# Returns default action or action assigned to first modifier
		if self.default:
			return self.default.strip()
		if len(self.order) > 0:
			return self.mods[self.order[0]].strip()
		# Empty ModeModifier
		return NoAction()
	
	
	def compress(self):
		if self.default:
			self.default = self.default.compress()
		for button in self.mods:
			self.mods[button] = self.mods[button].compress()
		return self
	
	
	def __str__(self):
		rv = [ ]
		for key in self.mods:
			rv += [ key.name, self.mods[key] ]
		if self.default is not None:
			rv += [ self.default ]
		return "<Modifier '%s', %s>" % (self.COMMAND, rv)
	
	__repr__ = __str__
	
	
	def describe(self, context):
		l = []
		if self.default : l.append(self.default)
		for x in self.order:
			l.append(self.mods[x])
		return "\n".join([ x.describe(context) for x in l ])
	
	
	def to_string(self, multiline=False, pad=0):
		if multiline:
			rv = [ (" " * pad) + "mode(" ]
			for key in self.mods:
				a_str = self.mods[key].to_string(True).split("\n")
				a_str[0] = (" " * pad) + "  " + (key.name + ",").ljust(11) + a_str[0]	# Key has to be one of SCButtons
				for i in xrange(1, len(a_str)):
					a_str[i] = (" " * pad) + "  " + a_str[i]
				a_str[-1] = a_str[-1] + ","
				rv += a_str
			if self.default is not None:
				a_str = [
					(" " * pad) + "  " + x
					for x in  self.default.to_string(True).split("\n")
				]
				rv += a_str
			if rv[-1][-1] == ",":
				rv[-1] = rv[-1][0:-1]
			rv += [ (" " * pad) + ")" ]
			return "\n".join(rv)
		else:
			rv = [ ]
			for key in self.mods:
				rv += [ key.name, self.mods[key].to_string(False) ]
			if self.default is not None:
				rv += [ self.default.to_string(False) ]
			return "mode(" + ", ".join(rv) + ")"
	
	
	def encode(self):
		rv = self.default.encode()
		rv['modes'] = {}
		for key in self.mods:
			rv['modes'][key.name] = self.mods[key].encode()
		if self.name: rv['name'] = self.name
		return rv
	
	
	def select(self, mapper):
		"""
		Selects action by pressed button.
		"""
		for b in self.order:
			if mapper.is_pressed(b):
				return self.mods[b]
		return self.default
	
	
	def select_b(self, mapper):
		"""
		Same as select but returns button as well.
		"""
		for b in self.order:
			if mapper.is_pressed(b):
				return b, self.mods[b]
		return None, self.default
	
	
	def button_press(self, mapper):
		sel = self.select(mapper)
		self.held_buttons.add(sel)
		return sel.button_press(mapper)
	
	
	def button_release(self, mapper):
		# Releases all held buttons, not just button that matches
		# currently pressed modifier
		for b in self.held_buttons:
			b.button_release(mapper)
	
	
	def trigger(self, mapper, position, old_position):
		if position < ModeModifier.MIN_TRIGGER:
			for b in self.held_triggers:
				b.trigger(mapper, 0, self.held_triggers[b])
			self.held_triggers = {}
			return False
		else:
			sel = self.select(mapper)
			self.held_triggers[sel] = position
			return sel.trigger(mapper, position, old_position)
		
	
	def axis(self, mapper, position, what):
		return self.select(mapper).axis(mapper, position, what)
	
	
	def gyro(self, mapper, pitch, yaw, roll, *q):
		sel = self.select(mapper)
		if sel is not self.old_gyro:
			if self.old_gyro:
				self.old_gyro.gyro(mapper, 0, 0, 0, *q)
			self.old_gyro = sel
		return sel.gyro(mapper, pitch, yaw, roll, *q)
	
	def pad(self, mapper, position, what):
		return self.select(mapper).pad(mapper, position, what)
	
	def whole(self, mapper, x, y, what):
		if what == STICK:
			if abs(x) < ModeModifier.MIN_STICK and abs(y) < ModeModifier.MIN_STICK:
				for b in self.held_sticks:
					b.whole(mapper, 0, 0, what)
				self.held_sticks.clear()
			else:
				self.held_sticks.add(self.select(mapper))
				for b in self.held_sticks:
					b.whole(mapper, x, y, what)
		else:
			return self.select(mapper).whole(mapper, x, y, what)


class SensitivityModifier(Modifier):
	COMMAND = "sens"
	def __init__(self, *parameters):
		# TODO: remove self.speeds
		self.speeds = []
		action = NoAction()
		for p in parameters:
			if type(p) in (int, float) and len(self.speeds) < 3:
				self.speeds.append(float(p))
			else:
				if isinstance(p, Action):
					action = p
		while len(self.speeds) < 3:
			self.speeds.append(1.0)
		Modifier.__init__(self, action)
		action.set_speed(*self.speeds)
		self.parameters = parameters
	
	
	def strip(self):
		return self.action.strip()
	
	
	def describe(self, context):
		if self.name: return self.name
		return self.action.describe(context)
	
	
	def to_string(self, multiline=False, pad=0):
		if multiline:
			childstr = self.action.to_string(True, pad + 2)
			if "\n" in childstr:
				return ((" " * pad) + "sens(" +
					(", ".join([ str(p) for p in self.parameters[0:-1] ])) + ",\n" +
					childstr + "\n" + (" " * pad) + ")")
		return Modifier.to_string(self, multiline, pad)
	
	
	def __str__(self):
		return "<Sensitivity=%s, %s>" % (self.speeds, self.action)
	
	def encode(self):
		rv = Modifier.encode(self)
		rv['sensitivity'] = self.speeds
		return rv
	
	def compress(self):
		return self.action.compress()


class FeedbackModifier(Modifier):
	COMMAND = "feedback"
	
	def __init__(self, *parameters):
		if len(parameters) < 2:
			raise TypeError("Not enought parameters")
		self.action = parameters[-1]
		self.haptic = HapticData(*parameters[:-1])
		self.action.set_haptic(self.haptic)
		
		Modifier.__init__(self, self.action)
		self.parameters = parameters


	def describe(self, context):
		if self.name: return self.name
		return self.action.describe(context)
	
	
	def to_string(self, multiline=False, pad=0):
		# Convert all but last parameters to string, using int() for amplitude and period
		pars = list(self.parameters[0:-1])
		if len(pars) >= 1: pars[0] = str(pars[0])		# Side
		if len(pars) >= 2: pars[1] = str(int(pars[1]))	# Amplitude
		if len(pars) >= 3: pars[2] = str(pars[2])		# Frequency
		if len(pars) >= 4: pars[3] = str(int(pars[3]))	# period
		
		if multiline:
			childstr = self.action.to_string(True, pad + 2)
			if "\n" in childstr:
				return ((" " * pad) + "feedback(" +
					", ".join(pars) + ",\n" +
					childstr + "\n" + (" " * pad) + ")")
		return ("feedback(" + ", ".join(pars) + ", " +
			self.action.to_string(False) + ")")
	
	
	def __str__(self):
		return "<with Feedback %s>" % (self.action,)
	
	def encode(self):
		rv = Modifier.encode(self)
		rv['feedback'] = list(self.parameters[0:-1])
		if self.haptic.get_position() == HapticPos.LEFT:
			rv['feedback'][0] = "LEFT"
		elif self.haptic.get_position() == HapticPos.RIGHT:
			rv['feedback'][0] = "RIGHT"
		else:
			rv['feedback'][0] = "BOTH"
		return rv
	
	def strip(self):
		return self.action.strip()
	
	def compress(self):
		return self.action.compress()


# Add modifiers to ACTIONS dict
for i in [ globals()[x] for x in dir() if hasattr(globals()[x], 'COMMAND') ]:
	if i.COMMAND is not None:
		ACTIONS[i.COMMAND] = i
