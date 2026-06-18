import uuid

import pytest
from sqlalchemy import select

from app.core.security import PasswordService, create_access_token
from app.models import Mensaje, Tenant, User, UserTenant

pytestmark = pytest.mark.asyncio


async def _setup_two_users(db_session):
    """Create a tenant with two users (sender and recipient)."""
    tenant = Tenant(name="MsgTest", code=f"MSG-{uuid.uuid4().hex[:6].upper()}")
    db_session.add(tenant)
    await db_session.flush()

    user_a = User(
        tenant_id=tenant.id,
        email=f"alice-{uuid.uuid4().hex[:8]}@test.com",
        legajo=f"LEG-{uuid.uuid4().hex[:8]}",
        nombre="Alice",
        apellido="Smith",
        password_hash=PasswordService.hash("pass"),
    )
    db_session.add(user_a)
    await db_session.flush()

    user_b = User(
        tenant_id=tenant.id,
        email=f"bob-{uuid.uuid4().hex[:8]}@test.com",
        legajo=f"LEG-{uuid.uuid4().hex[:8]}",
        nombre="Bob",
        apellido="Jones",
        password_hash=PasswordService.hash("pass"),
    )
    db_session.add(user_b)
    await db_session.flush()

    for u in (user_a, user_b):
        ut = UserTenant(user_id=u.id, tenant_id=tenant.id, is_active=True)
        db_session.add(ut)
    await db_session.flush()

    return user_a, user_b, tenant


async def _setup_other_tenant_user(db_session):
    """Create a user in a different tenant for cross-tenant tests."""
    tenant = Tenant(name="OtherTenant", code=f"OTH-{uuid.uuid4().hex[:6].upper()}")
    db_session.add(tenant)
    await db_session.flush()

    user = User(
        tenant_id=tenant.id,
        email=f"other-{uuid.uuid4().hex[:8]}@test.com",
        legajo=f"LEG-{uuid.uuid4().hex[:8]}",
        nombre="Other",
        apellido="User",
        password_hash=PasswordService.hash("pass"),
    )
    db_session.add(user)
    await db_session.flush()

    ut = UserTenant(user_id=user.id, tenant_id=tenant.id, is_active=True)
    db_session.add(ut)
    await db_session.flush()

    return user, tenant


class TestEnviarMensaje:

    async def test_send_to_valid_user_returns_201(self, client, db_session):
        alice, bob, tenant = await _setup_two_users(db_session)
        token = create_access_token(alice.id, tenant.id, [])

        resp = await client.post(
            "/api/v1/inbox/",
            json={
                "destinatario_id": str(bob.id),
                "asunto": "Hola Bob",
                "cuerpo": "Este es un mensaje de prueba",
            },
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["asunto"] == "Hola Bob"
        assert data["cuerpo"] == "Este es un mensaje de prueba"
        assert data["remitente_id"] == str(alice.id)
        assert data["destinatario_id"] == str(bob.id)
        assert data["leido"] is False
        assert "hilo_id" in data
        assert data["is_deleted"] is False

    async def test_send_to_nonexistent_user_returns_404(self, client, db_session):
        alice, bob, tenant = await _setup_two_users(db_session)
        token = create_access_token(alice.id, tenant.id, [])

        fake_id = uuid.uuid4()
        resp = await client.post(
            "/api/v1/inbox/",
            json={
                "destinatario_id": str(fake_id),
                "asunto": "Test",
                "cuerpo": "Body",
            },
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 404

    async def test_send_to_user_in_other_tenant_returns_404(self, client, db_session):
        alice, bob, tenant = await _setup_two_users(db_session)
        other, _ = await _setup_other_tenant_user(db_session)
        token = create_access_token(alice.id, tenant.id, [])

        resp = await client.post(
            "/api/v1/inbox/",
            json={
                "destinatario_id": str(other.id),
                "asunto": "Test",
                "cuerpo": "Body",
            },
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 404

    async def test_send_without_auth_returns_401(self, client, db_session):
        resp = await client.post(
            "/api/v1/inbox/",
            json={
                "destinatario_id": str(uuid.uuid4()),
                "asunto": "Test",
                "cuerpo": "Body",
            },
        )
        assert resp.status_code == 401


class TestListarInbox:

    async def test_inbox_returns_hilos_ordered_by_recent(self, client, db_session):
        alice, bob, tenant = await _setup_two_users(db_session)
        token_bob = create_access_token(bob.id, tenant.id, [])
        token_alice = create_access_token(alice.id, tenant.id, [])

        # Alice sends first message
        await client.post(
            "/api/v1/inbox/",
            json={
                "destinatario_id": str(bob.id),
                "asunto": "Mensaje 0",
                "cuerpo": "Cuerpo 0",
            },
            headers={"Authorization": f"Bearer {token_alice}"},
        )

        # Alice sends second message
        await client.post(
            "/api/v1/inbox/",
            json={
                "destinatario_id": str(bob.id),
                "asunto": "Mensaje 1",
                "cuerpo": "Cuerpo 1",
            },
            headers={"Authorization": f"Bearer {token_alice}"},
        )

        # Bob's inbox should have 2 hilos, most recent first
        resp = await client.get(
            "/api/v1/inbox/",
            headers={"Authorization": f"Bearer {token_bob}"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 2
        # Most recent first
        assert data[0]["ultimo_mensaje"] == "Cuerpo 1"

    async def test_inbox_with_pagination(self, client, db_session):
        alice, bob, tenant = await _setup_two_users(db_session)
        token_bob = create_access_token(bob.id, tenant.id, [])
        token_alice = create_access_token(alice.id, tenant.id, [])

        for i in range(3):
            await client.post(
                "/api/v1/inbox/",
                json={
                    "destinatario_id": str(bob.id),
                    "asunto": f"Msg {i}",
                    "cuerpo": f"Body {i}",
                },
                headers={"Authorization": f"Bearer {token_alice}"},
            )

        resp = await client.get(
            "/api/v1/inbox/?offset=0&limit=2",
            headers={"Authorization": f"Bearer {token_bob}"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 2

    async def test_inbox_empty_returns_empty_list(self, client, db_session):
        alice, bob, tenant = await _setup_two_users(db_session)
        token = create_access_token(alice.id, tenant.id, [])

        resp = await client.get(
            "/api/v1/inbox/",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 200
        assert resp.json() == []


class TestLeerHilo:

    async def test_read_own_hilo_returns_messages_ordered_asc_and_marks_read(
        self, client, db_session
    ):
        alice, bob, tenant = await _setup_two_users(db_session)
        token_alice = create_access_token(alice.id, tenant.id, [])
        token_bob = create_access_token(bob.id, tenant.id, [])

        # Alice sends to Bob
        resp = await client.post(
            "/api/v1/inbox/",
            json={
                "destinatario_id": str(bob.id),
                "asunto": "Test thread",
                "cuerpo": "First message",
            },
            headers={"Authorization": f"Bearer {token_alice}"},
        )
        hilo_id = resp.json()["hilo_id"]

        # Bob reads the hilo — should mark as read
        resp = await client.get(
            f"/api/v1/inbox/{hilo_id}",
            headers={"Authorization": f"Bearer {token_bob}"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 1
        assert data[0]["cuerpo"] == "First message"
        assert data[0]["leido"] is True  # Was marked read

    async def test_read_hilo_from_another_user_returns_404(self, client, db_session):
        alice, bob, tenant = await _setup_two_users(db_session)
        token_alice = create_access_token(alice.id, tenant.id, [])

        # Create a random hilo
        resp = await client.post(
            "/api/v1/inbox/",
            json={
                "destinatario_id": str(bob.id),
                "asunto": "Private",
                "cuerpo": "Secret",
            },
            headers={"Authorization": f"Bearer {token_alice}"},
        )
        hilo_id = resp.json()["hilo_id"]

        # A third user (not alice, not bob) cannot read
        other, other_tenant = await _setup_other_tenant_user(db_session)
        token_other = create_access_token(other.id, other_tenant.id, [])

        resp = await client.get(
            f"/api/v1/inbox/{hilo_id}",
            headers={"Authorization": f"Bearer {token_other}"},
        )
        assert resp.status_code == 404

    async def test_read_nonexistent_hilo_returns_404(self, client, db_session):
        alice, bob, tenant = await _setup_two_users(db_session)
        token = create_access_token(alice.id, tenant.id, [])

        fake_hilo = uuid.uuid4()
        resp = await client.get(
            f"/api/v1/inbox/{fake_hilo}",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 404


class TestResponderHilo:

    async def test_respond_in_hilo_returns_201_with_same_hilo_id(
        self, client, db_session
    ):
        alice, bob, tenant = await _setup_two_users(db_session)
        token_alice = create_access_token(alice.id, tenant.id, [])
        token_bob = create_access_token(bob.id, tenant.id, [])

        # Alice sends to Bob
        resp = await client.post(
            "/api/v1/inbox/",
            json={
                "destinatario_id": str(bob.id),
                "asunto": "Reply test",
                "cuerpo": "Hello Bob",
            },
            headers={"Authorization": f"Bearer {token_alice}"},
        )
        hilo_id = resp.json()["hilo_id"]

        # Bob replies
        resp = await client.post(
            f"/api/v1/inbox/{hilo_id}/responder",
            json={"cuerpo": "Hi Alice!"},
            headers={"Authorization": f"Bearer {token_bob}"},
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["hilo_id"] == hilo_id
        assert data["cuerpo"] == "Hi Alice!"
        assert data["remitente_id"] == str(bob.id)
        assert data["destinatario_id"] == str(alice.id)

    async def test_respond_without_access_returns_404(self, client, db_session):
        alice, bob, tenant = await _setup_two_users(db_session)
        token_alice = create_access_token(alice.id, tenant.id, [])

        # Create a hilo between alice and bob
        resp = await client.post(
            "/api/v1/inbox/",
            json={
                "destinatario_id": str(bob.id),
                "asunto": "Private",
                "cuerpo": "Secret",
            },
            headers={"Authorization": f"Bearer {token_alice}"},
        )
        hilo_id = resp.json()["hilo_id"]

        # A stranger cannot reply
        stranger, str_tenant = await _setup_other_tenant_user(db_session)
        token_stranger = create_access_token(stranger.id, str_tenant.id, [])

        resp = await client.post(
            f"/api/v1/inbox/{hilo_id}/responder",
            json={"cuerpo": "Hacked!"},
            headers={"Authorization": f"Bearer {token_stranger}"},
        )
        assert resp.status_code == 404

    async def test_respond_to_nonexistent_hilo_returns_404(self, client, db_session):
        alice, bob, tenant = await _setup_two_users(db_session)
        token = create_access_token(alice.id, tenant.id, [])

        fake_hilo = uuid.uuid4()
        resp = await client.post(
            f"/api/v1/inbox/{fake_hilo}/responder",
            json={"cuerpo": "Hello?"},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 404

    async def test_respond_swaps_sender_recipient_correctly(self, client, db_session):
        alice, bob, tenant = await _setup_two_users(db_session)
        token_alice = create_access_token(alice.id, tenant.id, [])
        token_bob = create_access_token(bob.id, tenant.id, [])

        # Alice sends to Bob
        resp = await client.post(
            "/api/v1/inbox/",
            json={
                "destinatario_id": str(bob.id),
                "asunto": "Swap test",
                "cuerpo": "First",
            },
            headers={"Authorization": f"Bearer {token_alice}"},
        )
        hilo_id = resp.json()["hilo_id"]

        # Bob replies → now Bob is sender, Alice is recipient
        resp = await client.post(
            f"/api/v1/inbox/{hilo_id}/responder",
            json={"cuerpo": "Reply from Bob"},
            headers={"Authorization": f"Bearer {token_bob}"},
        )
        assert resp.status_code == 201
        reply = resp.json()
        assert reply["remitente_id"] == str(bob.id)
        assert reply["destinatario_id"] == str(alice.id)

        # Alice replies → back to Alice sender, Bob recipient
        resp = await client.post(
            f"/api/v1/inbox/{hilo_id}/responder",
            json={"cuerpo": "Reply from Alice"},
            headers={"Authorization": f"Bearer {token_alice}"},
        )
        assert resp.status_code == 201
        reply2 = resp.json()
        assert reply2["remitente_id"] == str(alice.id)
        assert reply2["destinatario_id"] == str(bob.id)


class TestNoLeidos:

    async def test_unread_count_increments_on_receive_and_decrements_on_read(
        self, client, db_session
    ):
        alice, bob, tenant = await _setup_two_users(db_session)
        token_alice = create_access_token(alice.id, tenant.id, [])
        token_bob = create_access_token(bob.id, tenant.id, [])

        # Check Bob's inbox — should be empty
        resp = await client.get(
            "/api/v1/inbox/",
            headers={"Authorization": f"Bearer {token_bob}"},
        )
        assert resp.status_code == 200
        assert resp.json() == []

        # Alice sends message to Bob
        resp = await client.post(
            "/api/v1/inbox/",
            json={
                "destinatario_id": str(bob.id),
                "asunto": "Unread test",
                "cuerpo": "Check unread",
            },
            headers={"Authorization": f"Bearer {token_alice}"},
        )
        hilo_id = resp.json()["hilo_id"]

        # Bob's inbox should now have 1 hilo with 1 unread
        resp = await client.get(
            "/api/v1/inbox/",
            headers={"Authorization": f"Bearer {token_bob}"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 1
        assert data[0]["no_leidos"] == 1

        # Bob reads the hilo
        resp = await client.get(
            f"/api/v1/inbox/{hilo_id}",
            headers={"Authorization": f"Bearer {token_bob}"},
        )
        assert resp.status_code == 200

        # Now unread should be 0
        resp = await client.get(
            "/api/v1/inbox/",
            headers={"Authorization": f"Bearer {token_bob}"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data[0]["no_leidos"] == 0
