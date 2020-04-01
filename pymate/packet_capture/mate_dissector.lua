
DissectorTable.new("matenet")
mate_proto = Proto("matenet", "Outback MATE serial protocol")

local COMMANDS = {
    [0] = "Inc/Dis",  -- Increment or Disable (depending on the register)
    [1] = "Dec/En",   -- Decrement or Enable
    [2] = "Read",
    [3] = "Write",
    [4] = "Status",
    [22] = "Get Logpage"
}

local CMD_READ = 2
local CMD_WRITE = 3
local CMD_STATUS = 4

local DEVICE_TYPES = {
    [1] = "Hub",
    [2] = "(FX) FX Inverter",
    [3] = "(CC) MX Charge Controller",
    [4] = "(DC) FLEXnet DC"
}
local DEVICE_TYPES_SHORT = {
    [1] = "HUB",
    [2] = "FX",
    [3] = "CC",
    [4] = "DC"
}

local DTYPE_HUB = 1
local DTYPE_FX = 2
local DTYPE_CC = 3
local DTYPE_DC = 4

local REG_DEVICE_TYPE = 0x0000

local MX_STATUS = {
    [0] = "Sleeping",
    [1] = "Floating",
    [2] = "Bulk",
    [3] = "Absorb",
    [4] = "Equalize",
}

local MX_AUX_MODE = {
    [0] = "Disabled",
    [1] = "Diversion",
    [2] = "Remote",
    [3] = "Manual",
    [4] = "Fan",
    [5] = "PV Trigger",
    [6] = "Float",
    [7] = "ERROR Output",
    [8] = "Night Light",
    [9] = "PWM Diversion",
    [10] = "Low Battery",

    -- If MX sets mode to On/Off (not Auto)
    [0x3F] = "Manual",
}

local MX_AUX_STATE = {
    [0] = "Off",
    [0x40] = "On",
}

local FX_OPERATIONAL_MODE = {
    [0] = "Inverter Off",
    [1] = "Inverter Search",
    [2] = "Inverter On",
    [3] = "Charge",
    [4] = "Silent",
    [5] = "Float",
    [6] = "Equalize",
    [7] = "Charger Off",
    [8] = "Support AC",          -- FX is drawing power from batteries to support AC
    [9] = "Sell Enabled",     -- FX is exporting more power than the loads are drawing
    [10] = "Pass Through",       -- FX converter is off, passing through line AC
}

local FX_AC_MODE = {
    [0] = "No AC",
    [1] = "AC Drop",
    [2] = "AC Use",
}

local QUERY_REGISTERS = {
    -- MX/FX (Not DC)
    [0x0000] = "Device Type",
    -- [0x0001] = "FW Revision",

    -- FX
    -- [0x0039] = "Errors",
    -- [0x0059] = "Warnings",
    -- [0x003D] = "Inverter Control",
    -- [0x003A] = "AC In Control",
    -- [0x003C] = "Charge Control",
    -- [0x005A] = "AUX Mode",
    -- [0x0038] = "Equalize Control",
    -- [0x0084] = "Disconn Status",
    -- [0x008F] = "Sell Status",
    -- [0x0032] = "Battery Temperature",
    -- [0x0033] = "Air Temperature",
    -- [0x0034] = "MOSFET Temperature",
    -- [0x0035] = "Capacitor Temperature",
    -- [0x002D] = "Output Voltage",
    -- [0x002C] = "Input Voltage",
    -- [0x006D] = "Inverter Current",
    -- [0x006A] = "Charger Current",
    -- [0x006C] = "Input Current",
    -- [0x006B] = "Sell Current",
    -- [0x0019] = "Battery Actual",
    -- [0x0016] = "Battery Temperature Compensated",
    -- [0x000B] = "Absorb Setpoint",
    -- [0x0070] = "Absorb Time Remaining",
    -- [0x000A] = "Float Setpoint",
    -- [0x006E] = "Float Time Remaining",
    -- [0x000D] = "Refloat Setpoint",
    -- [0x000C] = "Equalize Setpoint",
    -- [0x0071] = "Equalize Time Remaining",

    -- MX
    -- [0x0008] = "Battery Voltage",
    -- [0x000F] = "Max Battery",
    -- [0x0010] = "V OC",
    -- [0x0012] = "Max V OC",
    -- [0x0013] = "Total kWh DC",
    -- [0x0014] = "Total kAh",
    -- [0x0015] = "Max Wattage",
    -- [0x016A] = "Charger Watts",
    -- [0x01EA] = "Charger kWh",
    -- [0x01C7] = "Charger Amps DC",
    -- [0x01C6] = "Panel Voltage",
    -- [0x01C8] = "Status",
    -- [0x01C9] = "Aux Relay Mode",
    -- [0x0170] = "Setpoint Absorb",
    -- [0x0172] = "Setpont Float",
}

-- Remember which device types are attached to each port
-- (Only available if you capture this data on startup!)
local device_table = {}
local device_table_available = false


local pf = {
    --bus = ProtoField.uint8("matenet.bus", "Bus", base.HEX),
    port                    = ProtoField.uint8("matenet.port", "Port", base.DEC),
    cmd                     = ProtoField.uint8("matenet.cmd", "Command", base.HEX, COMMANDS),
    device_type             = ProtoField.uint8("matenet.device_type", "Device Type", base.HEX, DEVICE_TYPES_SHORT),
    data                    = ProtoField.bytes("matenet.data", "Data", base.NONE),
    addr                    = ProtoField.uint16("matenet.addr", "Address", base.HEX),
    reg_addr                = ProtoField.uint16("matenet.register", "Register", base.HEX, QUERY_REGISTERS),
    value                   = ProtoField.uint16("matenet.value", "Value", base.HEX),
    check                   = ProtoField.uint16("matenet.checksum", "Checksum", base.HEX),

    mxstatus_ah             = ProtoField.float("matenet.mxstatus.amp_hours",    "Amp Hours",        {"Ah"}),
    mxstatus_pv_current     = ProtoField.int8("matenet.mxstatus.pv_current",    "PV Current",       base.UNIT_STRING, {"A"}),
    mxstatus_bat_current    = ProtoField.float("matenet.mxstatus.bat_current",  "Battery Current",  {"A"}),
    mxstatus_kwh            = ProtoField.float("matenet.mxstatus.kwh",          "Kilowatt Hours",   {"kWh"}),
    mxstatus_bat_voltage    = ProtoField.float("matenet.mxstatus.bat_voltage",  "Battery Voltage",  {"V"}),
    mxstatus_pv_voltage     = ProtoField.float("matenet.mxstatus.pv_voltage",   "PV Voltage",       {"V"}),
    mxstatus_aux            = ProtoField.uint8("matenet.mxstatus.aux",          "Aux",              base.DEC),
    mxstatus_aux_state      = ProtoField.uint8("matenet.mxstatus.aux_state",    "Aux State",        base.DEC, MX_AUX_STATE, 0x40),
    mxstatus_aux_mode       = ProtoField.uint8("matenet.mxstatus.aux_mode",     "Aux Mode",         base.DEC, MX_AUX_MODE, 0x3F),
    mxstatus_status         = ProtoField.uint8("matenet.mxstatus.status",       "Status",           base.DEC, MX_STATUS),
    mxstatus_errors         = ProtoField.uint8("matenet.mxstatus.errors",       "Errors",           base.DEC),
    mxstatus_errors_1       = ProtoField.uint8("matenet.mxstatus.errors.e3",    "High VOC",         base.DEC, NULL, 128),
    mxstatus_errors_2       = ProtoField.uint8("matenet.mxstatus.errors.e2",    "Too Hot",          base.DEC, NULL, 64),
    mxstatus_errors_3       = ProtoField.uint8("matenet.mxstatus.errors.e1",    "Shorted Battery Sensor", base.DEC, NULL, 32),

    fxstatus_misc           = ProtoField.uint8("matenet.fxstatus.flags",        "Flags",                base.DEC),
    fxstatus_is_230v        = ProtoField.uint8("matenet.fxstatus.misc.is_230v", "Is 230V",              base.DEC, NULL, 0x01),
    fxstatus_aux_on         = ProtoField.uint8("matenet.fxstatus.misc.aux_on",  "Aux On",               base.DEC, NULL, 0x80),
    fxstatus_warnings       = ProtoField.uint8("matenet.fxstatus.warnings",     "Warnings",             base.DEC),
    fxstatus_errors         = ProtoField.uint8("matenet.fxstatus.errors",       "Errors",               base.DEC),
    fxstatus_ac_mode        = ProtoField.uint8("matenet.fxstatus.ac_mode",      "AC Mode",              base.DEC, FX_AC_MODE),
    fxstatus_op_mode        = ProtoField.uint8("matenet.fxstatus.op_mode",      "Operational Mode",     base.DEC, FX_OPERATIONAL_MODE),
    fxstatus_inv_current    = ProtoField.float("matenet.fxstatus.inv_current",  "Inverter Current",     {"A"}),
    fxstatus_out_voltage    = ProtoField.float("matenet.fxstatus.out_voltage",  "Out Voltage",          {"V"}),
    fxstatus_in_voltage     = ProtoField.float("matenet.fxstatus.in_voltage",   "In Voltage",           {"V"}),
    fxstatus_sell_current   = ProtoField.float("matenet.fxstatus.sell_current", "Sell Current",         {"A"}),
    fxstatus_chg_current    = ProtoField.float("matenet.fxstatus.chg_current",  "Charge Current",       {"A"}),
    fxstatus_buy_current    = ProtoField.float("matenet.fxstatus.buy_current",  "Buy Current",          {"A"}),
    fxstatus_bat_voltage    = ProtoField.float("matenet.fxstatus.bat_voltage",  "Battery Voltage",      {"V"}),

    -- dcstatus_shunta_kw
    -- dcstatus_shuntb_kw
    -- dcstatus_shuntc_kw
    -- dcstatus_shunta_cur
    -- dcstatus_shuntb_cur
    -- dcstatus_shuntc_cur
    -- dcstatus_bat_v
    -- dcstatus_soc
    -- dcstatus_now_out_kw_lo
    -- dcstatus_now_out_kw_hi
    -- dcstatus_now_in_kw
    -- dcstatus_bat_cur
    -- dcstatus_out_cur
    -- dcstatus_in_cur
    -- dcstatus_flags
    -- dcstatus_unknown1
    -- dcstatus_today_out_kwh
    -- dcstatus_today_in_kwh
    -- dcstatus_today_bat_ah
    -- dcstatus_today_out_ah
    -- dcstatus_today_in_ah
    -- dcstatus_now_bat_kw
    -- dcstatus_unknown2
    -- dcstatus_days_since_full
    -- dcstatus_today_bat_kwh
    -- dcstatus_shunta_ah
    -- dcstatus_shuntb_ah
    -- dcstatus_shuntc_ah
    -- dcstatus_shunta_kwh
    -- dcstatus_shuntb_kwh
    -- dcstatus_shuntc_kwh
    -- dcstatus_unknown3
    -- dcstatus_bat_net_kwh
    -- dcstatus_bat_net_ah
    -- dcstatus_min_soc_today
}
mate_proto.fields = pf

function fmt_cmd(cmd, prior_cmd)
    if prior_cmd then
    end
    return COMMANDS[cmd:uint()]
end



function fmt_addr(cmd)
    -- INC/DEC/READ/WRITE : Return readable register name
    if cmd:uint() <= 3 then
        name = QUERY_REGISTERS[addr:uint()]
        if name then
            return name
        end
    end

    return addr
end

function fmt_mx_status()
    -- TODO: Friendly MX status string
    return "MX STATUS"
end

function fmt_response(port, cmd, addr, resp_data)
    cmd = cmd:uint()
    addr = addr:uint()

    -- QUERY DEVICE TYPE
    if (cmd == CMD_READ) and (addr == REG_DEVICE_TYPE) then
        -- Remember the device attached to this port
        local dtype = resp_data:uint()
        device_table[port:uint()] = dtype
        device_table_available = true

        return DEVICE_TYPES[dtype]
    end
    
    if device_table_available then
        local dtype = device_table[port:uint()]
        if (cmd == CMD_STATUS) then
            -- Format status packets
            if dtype == DTYPE_CC then
                --return fmt_mx_status(resp_data)
            end
        end
    end

    return resp_data
end

function fmt_dest(port)
    local dtype = device_table[port:uint()]
    if dtype then
        return "Port " .. port .. " (" .. DEVICE_TYPES_SHORT[dtype] .. ")"
    else
        return "Port " .. port
    end
end

function parse_mx_status(addr, data, tree)
    local raw_ah = bit.bor(
        bit.rshift(bit.band(data(0,1):uint(), 0x70), 4), -- ignore bit7
        data(4,1):uint()
    )

    local raw_kwh = bit.bor(
        bit.lshift(data(3,1):uint(), 8),
        data(8,1):uint()
    ) / 10.0

    local bat_curr_milli = bit.band(data(0,1):uint(), 0x0F) / 10.0

    tree:add(pf.mxstatus_pv_current,  data(1,1), (data(1,1):int()+128))
    tree:add(pf.mxstatus_bat_current, data(2,1), (data(2,1):int()+128 + bat_curr_milli))

    tree:add(pf.mxstatus_ah, data(4,1), raw_ah)  -- composite value
    tree:add(pf.mxstatus_kwh, data(8,1), raw_kwh) -- composite value

    tree:add(pf.mxstatus_status, data(6,1))

    local error_node = tree:add(pf.mxstatus_errors, data(7,1))
    error_node:add(pf.mxstatus_errors_1, data(7,1))
    error_node:add(pf.mxstatus_errors_2, data(7,1))
    error_node:add(pf.mxstatus_errors_3, data(7,1))

    local aux_node = tree:add(pf.mxstatus_aux, data(5,1))
    aux_node:add(pf.mxstatus_aux_state, data(5,1))
    aux_node:add(pf.mxstatus_aux_mode, data(5,1))

    tree:add(pf.mxstatus_bat_voltage, data(9,2), (data(9,2):uint()/10.0))
    tree:add(pf.mxstatus_pv_voltage, data(11,2), (data(11,2):uint()/10.0))
end

function parse_fx_status(addr, data, tree)
    local misc_node = tree:add(pf.fxstatus_misc, data(11,1))
    misc_node:add(pf.fxstatus_is_230v, data(11,1))
    misc_node:add(pf.fxstatus_aux_on, data(11,1))

    -- If 230V bit is set, voltages must be multiplied by 2, and currents divided by 2.
    local is_230v = bit.band(data(11,1):uint(), 0x01)
    local vmul = 1.0
    local imul = 1.0
    if is_230v then
        vmul = 2.0
        imul = 0.5
    end

    tree:add(pf.fxstatus_inv_current, data(0,1), data(0,1):uint()*imul)
    tree:add(pf.fxstatus_chg_current, data(1,1), data(1,1):uint()*imul)
    tree:add(pf.fxstatus_buy_current, data(2,1), data(2,1):uint()*imul)
    tree:add(pf.fxstatus_in_voltage, data(3,1), data(3,1):uint()*vmul)
    tree:add(pf.fxstatus_out_voltage, data(4,1), data(4,1):uint()*vmul)
    tree:add(pf.fxstatus_sell_current, data(5,1), data(5,1):uint()*imul)

    tree:add(pf.fxstatus_op_mode, data(6,1))
    tree:add(pf.fxstatus_ac_mode, data(8,1))
    tree:add(pf.fxstatus_bat_voltage, data(9,2), (data(9,2):uint()/10.0))
    
    local warn_node = tree:add(pf.fxstatus_warnings, data(12,1))
    -- TODO: Add warning bitfield
    -- WARN_ACIN_FREQ_HIGH         = 0x01 # >66Hz or >56Hz
    -- WARN_ACIN_FREQ_LOW          = 0x02 # <54Hz or <44Hz
    -- WARN_ACIN_V_HIGH            = 0x04 # >140VAC or >270VAC
    -- WARN_ACIN_V_LOW             = 0x08 # <108VAC or <207VAC
    -- WARN_BUY_AMPS_EXCEEDS_INPUT = 0x10
    -- WARN_TEMP_SENSOR_FAILED     = 0x20 # Internal temperature sensors have failed
    -- WARN_COMM_ERROR             = 0x40 # Communication problem between us and the FX
    -- WARN_FAN_FAILURE            = 0x80 # Internal cooling fan has failed

    local err_node = tree:add(pf.fxstatus_errors, data(7,1))
    -- TODO: Add error bitfield
    -- ERROR_LOW_VAC_OUTPUT = 0x01 # Inverter could not supply enough AC voltage to meet demand
    -- ERROR_STACKING_ERROR = 0x02 # Communication error among stacked FX inverters (eg. 3 phase system)
    -- ERROR_OVER_TEMP      = 0x04 # FX has reached maximum allowable temperature
    -- ERROR_LOW_BATTERY    = 0x08 # Battery voltage below low battery cut-out setpoint
    -- ERROR_PHASE_LOSS     = 0x10
    -- ERROR_HIGH_BATTERY   = 0x20 # Battery voltage rose above safe level for 10 seconds
    -- ERROR_SHORTED_OUTPUT = 0x40 
    -- ERROR_BACK_FEED      = 0x80 # Another power source was connected to the FX's AC output
end

function parse_dc_status(addr, data, tree)
    if addr == 0x0A then


    elseif addr == 0x0B then

    elseif addr == 0x0C then

    elseif addr == 0x0D then

    elseif addr == 0x0E then

    elseif addr == 0x0F then

    end
end

--local ef_too_short = ProtoExpert.new("mate.too_short.expert", "MATE packet too short",
--                                    expert.group.MALFORMED, expert.severity.ERROR)

local prior_cmd = nil
local propr_cmd_port = nil
local prior_cmd_addr = nil

function dissect_frame(bus, buffer, pinfo, tree, combine)
    -- MATE TX (Command)
    if bus == 0xA then
        if not combine then
            pinfo.cols.src = "MATE"
            pinfo.cols.dst = "Device"
        end
        
        local subtree = tree:add(mate_proto, buffer(), "Command")
        
        if buffer:len() <= 7 then
            return
        end

        port = buffer(0, 1)
        cmd  = buffer(1, 1)
        addr = buffer(2, 2)
        value = buffer(4, 2)
        check = buffer(6, 2)
        --data = buffer(4, buffer:len()-4)
        subtree:add(pf.port, port)
        subtree:add(pf.cmd,  cmd)
        --subtree:add(pf.data, data)

        --pinfo.cols.info:set("Command")
        info = fmt_cmd(cmd)
        if info then
            pinfo.cols.info:prepend(info .. " ")
        end

        -- INC/DEC/READ/WRITE
        if cmd:uint() <= 3 then
            subtree:add(pf.reg_addr, addr)
            pinfo.cols.info:append(" ["..fmt_addr(addr).."]")
        else
            subtree:add(pf.addr, addr)
        end

        subtree:add(pf.value, value)
        subtree:add(pf.check, check)

        pinfo.cols.dst = fmt_dest(port)

        prior_cmd = cmd
        prior_cmd_port = port
        prior_cmd_addr = addr
        
        return -1
        
    -- MATE RX (Response)
    elseif bus == 0xB then
        if not combine then
            pinfo.cols.src = "Device"
            pinfo.cols.dst = "MATE"
        end
        
        local subtree = tree:add(mate_proto, buffer(), "Response")

        if buffer:len() <= 3 then
            return
        end
        
        cmd = buffer(0, 1)
        if combine and (prior_cmd:uint() == CMD_STATUS) then
            -- For STATUS responses, this is the type of device that sent the status
            subtree:add(pf.device_type, cmd)
        else
            -- Otherwise it should match the command that this is responding to
            subtree:add(pf.cmd, cmd)
        end
    
        data = buffer(1, buffer:len()-3)
        check = buffer(buffer:len()-2, 2)
        local data_node = subtree:add(pf.data, data)
        subtree:add(pf.check, check)

        if not combine then
            pinfo.cols.info:set("Response")

            info = fmt_cmd(cmd, prior_cmd)
            if info then
                pinfo.cols.info:prepend(info .. " ")
            end
        else
            -- append the response value
            -- INC/DEC/READ/WRITE
            if cmd:uint() <= 3 then
                pinfo.cols.info:append(" : " .. fmt_response(
                    prior_cmd_port, 
                    prior_cmd, 
                    prior_cmd_addr, 
                    data
                ))
            end

            -- We know what type of device is attached to this port,
            -- so do some additional parsing...
            if device_table_available then
                local cmd = prior_cmd:uint()
                local addr = prior_cmd_addr:uint()
                local dtype = device_table[port:uint()]

                -- Parse status packets
                if (cmd == CMD_STATUS) then
                    if dtype == DTYPE_CC then
                        parse_mx_status(addr, data, data_node)
                    elseif dtype == DTYPE_FX then
                        parse_fx_status(addr, data, data_node)
                    elseif dtype == DTYPE_DC then
                        parse_dc_status(addr, data, data_node)
                    end
                end
            end
        end
    end
end

function mate_proto.dissector(buffer, pinfo, tree)
    len = buffer:len()
    if len == 0 then return end

    pinfo.cols.protocol = mate_proto.name

    --local subtree = tree:add(mate_proto, buffer(), "MATE Data")

    -- if len < 5 then
    --     subtree.add_proto_expert_info(ef_too_short)
    --     return
    -- end

    bus = buffer(0, 1):uint()
    --subtree:add(pf.bus, bus)
    buffer = buffer(1, buffer:len()-1)

    -- local data = {}
    -- for i=0,buffer:len() do
    --     data[i] = i
    -- end
    
    -- Combined RX/TX
    if bus == 0x0F then
        len_a = buffer(0, 1):uint()
        len_b = buffer(1, 1):uint()
        
        buf_a = buffer(2, len_a)
        buf_b = buffer(2+len_a, len_b)
        
        r_a = dissect_frame(0xA, buf_a, pinfo, tree, true)
        r_b = dissect_frame(0xB, buf_b, pinfo, tree, true)
        --return r_a + r_b
        
        pinfo.cols.src = "MATE"
        --pinfo.cols.dst = "Device"
        
    else
        return dissect_frame(bus, buffer, pinfo, tree, false)
    end


end

-- This function will be invoked by Wireshark during initialization, such as
-- at program start and loading a new file
function mate_proto.init()
    device_table = {}
    device_table_available = false
end


DissectorTable.get("matenet"):add(147, mate_proto) -- DLT_USER0