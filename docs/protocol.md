To control running daemon instance, unix socket in user directory is used.
Controlling protocol uses case-sensitive messages terminated by newline. Message type and message arguments are delimited by `:`.

When new connection is accepted, daemon sends some info:

```
SCCDaemon
Version: 0.1
PID: 123456
Current profile: filename.sccprofile
Ready.
```

Connection is then held until client side closes it.


# Messages sends by daemon:

#### `Current profile: filename.sccprofile`
Sent to every client when profile file is loaded and used. Automatically sent when connnection is accepted and when profile is changed.

#### `Event: source values`
Sent to client that requested locking of source (that is button, pad or axis).

List of possible events:
- `Event: B 1` - Sent when button is pressed. *B* is button, is one of *SCButtons.\** constants.
- `Event: B 0` - Sent when button is released. *B* is button one of *SCButtons.\** constants.
- `Event: STICK x y` - Sent when stick position is changed. *x* and *y* are new values.
- `Event: LEFT x y` - Sent when finger on left pad is moved. *x* and *y* is new position.
- `Event: RIGHT x y` - Sent when finger on right pad is moved. *x* and *y* is new position.

#### `Error: description`
Sent to every client when error is detected. May be sent repeadedly, until error condition is cleared.
After that, `Ready.` is sent to indicate that emulation works again.

#### `Fail: text`
Indicates error client that sent request.

#### `OK.`
Indicates sucess to client that sent request.

### `OSD: tool param1 param2...`
Send to scc-osd-daemon when osd-related action is requested.
*tool* can be *'message'* or *'menu'*, *params* are same as command-line arguments for related
scc-osd-* script.

#### `PID: xyz`
Reports PID of *scc-daemon* instance. Automatically sent when connnection is accepted.

#### `Ready.`
Automatically sent when connnection is accepted to indicate that there is no error and daemon is working as expected.

#### `SCCDaemon`
Just identification message, automatically sent when connnection is accepted.
Can be either ignored or used to check if remote side really is *scc-daemon*.

#### `Version: x.y`
Identifies daemon version. Automatically sent when connnection is accepted.

# Commands sent from client to daemon

#### `Lock: button1 button2...`
Locks physical button, axis or pad. Events from locked sources are not processed normally, but sent to client that initiated lock.

Only one client can have one source locked at one time. Second attempt to lock already locked source will fail and `Fail: cannot lock <button>` will be sent as response. Locking is done only if all requested sources are free and in such case, daemon responds with `OK.`

While source is locked, daemon keeps sending `Event: ...` messages every time when button is pressed, released, axis moved, etc...

Unlocking is done automatically when client is disconnected, or using `Unlock.` message.

#### `Profile: filename.sccprofile`
Asks daemon to load another profile. No escaping or quouting is needed, everything after colon is used as filename, only spaces and tabs are stripped.

If profile is sucessfully loaded, daemon responds with `OK.` to client that initiated loading and sends `Current profile: ...` message to all clients.

If loading fails, daemon responds with `Fail: ....` message where error with entire backtrace is sent. Backtrace is escaped to fit it on single line.

#### `Register: osd`
Send by scc-osd-daemon to register client connection as one made by scc-osd-daemon.
When sent by more than one client, daemon will automatically close forme connection
before registering new one.
Daemon responds with `OK.`

#### `Selected: menu_id item_id`
Send by scc-osd-daemon when user chooses item from displayed menu.
Daemon responds with `OK.`

#### `Unlock.`
Unlocks everything locked with `Lock...` messages sent by same client. This operation cannot fail (and does nothing if there is nothing to unlock), so daemon always responds with `OK.`
