from ..model.reaction_role import ReactionRole as _ReactionRole


def test() -> None:
    rr = _ReactionRole.make(
        guild_id=896010670909304863,
        channel_id=896010670909304863,
        message_id=896010670909304863,
        name="RR1234",
        reaction="🙂",
    )

    try:
        rr.message_id = 896806211058532452
        rr.name = "RR1345"
        rr.reaction = "🙃"
        rr.is_active = True
        rr.save()
    except Exception as e:
        rr.delete()
        raise e

    try:
        ch_1 = rr.add_change(680621105853242345, True, False)
    except Exception as e:
        rr.delete()
        raise e

    try:
        ch_1.role_id = 680621105853242456
        ch_1.add = False
        ch_1.allow_toggle = True
        ch_1.message_channel_id = 3456
        ch_1.message_content = "Test"
        ch_1.save()
    except Exception as e:
        rr.delete()
        raise e

    try:
        rr.remove_change(ch_1.id)
    except Exception as e:
        rr.delete()
        raise e

    try:
        req_1 = rr.add_requirement(76211058532452)
    except Exception as e:
        rr.delete()
        raise e

    try:
        rr.remove_requirement(req_1.id)
    except Exception as e:
        rr.delete()
        raise e

    ch_2 = rr.add_change(2345, True, False)
    req_2 = rr.add_requirement(6789)

    rr.delete()
