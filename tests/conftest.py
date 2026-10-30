import mimetypes
from urllib.parse import urlsplit

import pytest
import pytest_asyncio
from asgiref.sync import sync_to_async
from django.contrib.auth import get_user_model
from django.contrib.staticfiles import finders


@pytest.fixture
def staff(db):
    return get_user_model().objects.create_user(username="staff", is_staff=True)


@pytest.fixture
def superuser(staff):
    staff.is_superuser = True
    staff.save()
    return staff


@pytest_asyncio.fixture
async def admin_page(page, client, superuser):
    await sync_to_async(client.force_login)(superuser)

    async def respond(route):
        url = urlsplit(route.request.url)
        if url.path.startswith("/static/"):
            path = finders.find(url.path.removeprefix("/static/"))
            if path:
                await route.fulfill(path=path, content_type=mimetypes.guess_type(path)[0])
            else:
                await route.fulfill(status=404)
            return
        response = await sync_to_async(client.get)(url.path, QUERY_STRING=url.query)
        headers = {"Content-Type": response["Content-Type"]}
        if response.has_header("Location"):
            headers["Location"] = response["Location"]
        await route.fulfill(status=response.status_code, headers=headers, body=response.content)

    await page.context.route("http://testserver/**", respond)
    await page.goto("http://testserver/admin/")
    return page
