def test_authenticated_nav_contains_core_modules(authenticated_client):
    response = authenticated_client.get("/")

    assert response.status_code == 200
    html = response.get_data(as_text=True)
    assert "Dashboard" in html
    assert "Quick Log" in html
    assert "Goals" in html
    assert "Finance" in html
    assert "Body" in html
    assert "Workouts" in html
    assert "Logout" in html


def test_public_auth_pages_render_accessible_forms(client):
    login_response = client.get("/auth/login")
    register_response = client.get("/auth/register")

    assert login_response.status_code == 200
    assert register_response.status_code == 200

    login_html = login_response.get_data(as_text=True)
    register_html = register_response.get_data(as_text=True)

    assert "E-mail" in login_html
    assert "Senha" in login_html
    assert "name=\"email\"" in login_html
    assert "name=\"password\"" in login_html

    assert "Nome" in register_html
    assert "E-mail" in register_html
    assert "name=\"name\"" in register_html
    assert "name=\"password\"" in register_html
