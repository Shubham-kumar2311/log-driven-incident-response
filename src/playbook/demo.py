from playbook_engine import PlaybookEngine, Playbook, PlaybookStep
import uuid


def firewall_actuator(command: str, target: str) -> bool:
    print(f"[Firewall] {command} -> {target}")
    return True


def email_actuator(command: str, target: str) -> bool:
    print(f"[Email] {command} -> {target}")
    return True


def main():
    engine = PlaybookEngine()

    engine.register_actuator("firewall", firewall_actuator)
    engine.register_actuator("email", email_actuator)

    playbook = Playbook(
        playbook_id=str(uuid.uuid4()),
        name="High Severity Containment",
        trigger_severity="high"
    )

    playbook.add_step(
        PlaybookStep(
            step_id="1",
            action_type="firewall",
            target="192.168.1.10",
            command="block_ip",
            retry_count=2
        )
    )

    playbook.add_step(
        PlaybookStep(
            step_id="2",
            action_type="email",
            target="phishing_mail_id",
            command="delete_email",
            retry_count=1
        )
    )

    result = engine.execute(playbook, incident_id="INC-001")

    print("\nFinal Execution Result:")
    print(result)


if __name__ == "__main__":
    main()