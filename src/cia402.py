STATUSWORD_BITS = (
    (0, "ready_to_switch_on"),
    (1, "switched_on"),
    (2, "operation_enabled"),
    (3, "fault"),
    (4, "voltage_enabled"),
    (5, "quick_stop_not_active"),
    (6, "switch_on_disabled"),
    (7, "warning"),
    (8, "manufacturer_specific"),
    (9, "remote"),
    (10, "target_reached"),
    (11, "internal_limit_active"),
    (12, "operation_mode_specific_1"),
    (13, "operation_mode_specific_2"),
)


def decode_statusword_bits(value):
    return {
        name: bool(value & (1 << bit))
        for bit, name in STATUSWORD_BITS
    }


def statusword_state(value):
    if (value & 0x004F) == 0x0000:
        return "Not ready to switch on"
    if (value & 0x004F) == 0x0040:
        return "Switch on disabled"
    if (value & 0x006F) == 0x0021:
        return "Ready to switch on"
    if (value & 0x006F) == 0x0023:
        return "Switched on"
    if (value & 0x006F) == 0x0027:
        return "Operation enabled"
    if (value & 0x006F) == 0x0007:
        return "Quick stop active"
    if (value & 0x004F) == 0x000F:
        return "Fault reaction active"
    if (value & 0x004F) == 0x0008:
        return "Fault"
    return "Unknown / manufacturer-specific state"


def format_statusword(value):
    bits = decode_statusword_bits(value)
    active_bits = [name for name, active in bits.items() if active]
    bit_text = ", ".join(active_bits) if active_bits else "no status bits set"
    return f"0x{value:04X} - {statusword_state(value)} ({bit_text})"
