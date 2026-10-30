const dialog = document.getElementById("djangonaut");

if (dialog) {
  const { getResults } = await import(dialog.dataset.searchUrl);
  const catalog = JSON.parse(
    document.getElementById("djangonaut-data").textContent,
  );
  const input = dialog.querySelector("input");
  const closeButton = dialog.querySelector(".djangonaut-close");
  const helpButton = dialog.querySelector(".djangonaut-help-button");
  const list = dialog.querySelector("ul");
  const empty = dialog.querySelector(".djangonaut-empty");
  const guide = dialog.querySelector("#djangonaut-guide");
  let results = [];
  let selected = 0;
  let previousFocus;
  let helpOpen = false;

  function select(index) {
    selected = index;
    for (const [i, option] of Array.from(list.children).entries()) {
      option.setAttribute("aria-selected", String(i === selected));
    }
    const option = list.children[selected];
    if (option) {
      input.setAttribute("aria-activedescendant", option.id);
      option.scrollIntoView({ block: "nearest" });
    } else {
      input.removeAttribute("aria-activedescendant");
    }
  }

  function render() {
    const showHelp = helpOpen || input.value.trim() === "?";
    helpButton.setAttribute("aria-expanded", String(showHelp));
    guide.hidden = !showHelp;
    list.hidden = showHelp;
    input.setAttribute("aria-expanded", String(!showHelp));
    input.setAttribute(
      "aria-describedby",
      showHelp ? "djangonaut-guide" : "djangonaut-help",
    );
    results = showHelp ? [] : getResults(input.value, catalog);
    list.replaceChildren();
    empty.hidden = showHelp || results.length > 0;
    results.forEach((result, index) => {
      const option = document.createElement("li");
      option.id = `djangonaut-option-${index}`;
      option.setAttribute("role", "option");
      option.setAttribute("aria-disabled", String(!result.url));
      const label = document.createElement("span");
      label.className = "djangonaut-name";
      label.textContent = result.label;
      const app = document.createElement("span");
      app.className = "djangonaut-app";
      app.textContent = result.key;
      option.append(label, app);
      if (result.detail) {
        const detail = document.createElement("span");
        detail.className = "djangonaut-detail";
        detail.textContent = result.detail;
        option.append(detail);
      }
      option.addEventListener("pointermove", () => select(index));
      option.addEventListener("click", (event) =>
        choose(index, event.metaKey || event.ctrlKey),
      );
      list.append(option);
    });
    select(0);
  }

  function close() {
    dialog.close();
  }

  function choose(index, newTab) {
    const result = results[index];
    if (!result) return;
    if (!result.url) {
      input.focus();
      return;
    }
    if (newTab) {
      window.open(result.url, "_blank", "noopener");
    } else {
      window.location.assign(result.url);
    }
    close();
  }

  function open() {
    previousFocus = document.activeElement;
    input.value = "";
    helpOpen = false;
    dialog.showModal();
    input.setAttribute("aria-expanded", "true");
    render();
    input.focus();
  }

  function hideHelp() {
    helpOpen = false;
    if (input.value.trim() === "?") input.value = "";
    render();
    input.focus();
  }

  input.addEventListener("input", render);
  input.addEventListener("keydown", (event) => {
    if (event.isComposing) return;
    if (event.key === "ArrowDown" || event.key === "ArrowUp") {
      event.preventDefault();
      if (results.length) {
        select(
          (selected + (event.key === "ArrowDown" ? 1 : -1) + results.length) %
            results.length,
        );
      }
    } else if (event.key === "Enter") {
      event.preventDefault();
      choose(selected, event.metaKey || event.ctrlKey);
    }
  });

  closeButton.addEventListener("click", close);
  helpButton.addEventListener("click", () => {
    if (!guide.hidden) hideHelp();
    else {
      helpOpen = true;
      render();
      input.focus();
    }
  });
  dialog.addEventListener("cancel", (event) => {
    if (!guide.hidden) {
      event.preventDefault();
      hideHelp();
    }
  });
  dialog.addEventListener("keydown", (event) => {
    if (event.key !== "Tab") return;
    const controls = Array.from(
      dialog.querySelectorAll("input, button:not([hidden])"),
    );
    if (!event.shiftKey && document.activeElement === controls.at(-1)) {
      event.preventDefault();
      controls[0].focus();
    } else if (event.shiftKey && document.activeElement === controls[0]) {
      event.preventDefault();
      controls.at(-1).focus();
    }
  });
  dialog.addEventListener("close", () => {
    input.setAttribute("aria-expanded", "false");
    input.removeAttribute("aria-activedescendant");
    if (previousFocus?.isConnected) previousFocus.focus();
  });
  dialog.addEventListener("click", (event) => {
    if (event.target !== dialog) return;
    const rect = dialog.getBoundingClientRect();
    if (
      event.clientX < rect.left ||
      event.clientX > rect.right ||
      event.clientY < rect.top ||
      event.clientY > rect.bottom
    ) {
      close();
    }
  });
  document.addEventListener("keydown", (event) => {
    if (event.isComposing || event.repeat || event.altKey || event.shiftKey)
      return;
    if ((event.ctrlKey || event.metaKey) && event.key.toLowerCase() === "k") {
      event.preventDefault();
      dialog.open ? close() : open();
    }
  });
}
