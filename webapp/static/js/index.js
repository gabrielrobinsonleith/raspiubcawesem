var Index = {
    components: {
        btnElectronBeamOn: document.getElementById("btnElectronBeamOn"),
        btnElectronBeamAlign: document.getElementById("btnElectronBeamAlign"),
        btnStartScan: document.getElementById("btnStartScan"),
        btnStopScan: document.getElementById("btnStopScan"),
        btnSaveScan: document.getElementById("btnSaveScan"),
        formSaveScan: document.getElementById("formSaveScan"),
        sliderImageMagnify: document.getElementById("sliderImageMagnify"),
        sliderImageBrightness: document.getElementById("sliderImageBrightness"),
        sliderImageContrast: document.getElementById("sliderImageContrast"),
        radioScanRates: document.getElementsByName("scanRates"),
        radioScanRateCustom: document.getElementById("scanRateCustom"),
        displayAccelerationVoltage: document.getElementById("displayAccelerationVoltage"),
    },

    routes: {
        postElectronBeamOn: "/api/electron_beam_on",
        postElectronBeamOff: "/api/electron_beam_off",
        postElectronBeamAlign: "/api/electron_beam_align",
        postStartStream: "/api/start_stream",
        postStopStream: "/api/pause_stream",
        postSaveScan: "/api/save_scan",
        postImageMagnify: "/api/set_image_setting_magnify",
        postImageBrightness: "/api/set_image_setting_brightness",
        postImageContrast: "/api/set_image_setting_contrast",
        postScanRate: "/api/set_scan_rate",
        getBeamControlOutput: "/api/get_beam_control_output",
    },

    init: function() {
        this.bindUI();
        if (this.components.btnElectronBeamOn.innerText == "Power On") {
            this.disableMainElements(true);
        }
        else {
            // System has previously been powered on
            this.disableMainElements(false);
            Index.components.btnElectronBeamOn.classList.toggle("btn-dark")
            Index.components.btnElectronBeamOn.classList.toggle("btn-danger")
        }
        this.components.btnStopScan.disabled = true;
    },

    bindUI: function() {
        this.components.btnElectronBeamOn.addEventListener("click", this.onElectronBeamOnClick);
        this.components.btnElectronBeamAlign.addEventListener("click", this.onElectronBeamAlignClick);
        this.components.btnStartScan.addEventListener("click", this.onStartScanClick);
        this.components.btnStopScan.addEventListener("click", this.onStopScanClick);
        this.components.sliderImageMagnify.addEventListener("change", this.onImageMagnifyChange);
        this.components.sliderImageBrightness.addEventListener("change", this.onImageBrightnessChange);
        this.components.sliderImageContrast.addEventListener("change", this.onImageContrastChange);

        this.components.radioScanRates[0].addEventListener("click", this.onScanRateClick.slowest);
        this.components.radioScanRates[1].addEventListener("click", this.onScanRateClick.slow);
        this.components.radioScanRates[2].addEventListener("click", this.onScanRateClick.normal);
        this.components.radioScanRates[3].addEventListener("click", this.onScanRateClick.fast);
        this.components.radioScanRates[4].addEventListener("click", this.onScanRateClick.fastest);
        this.components.radioScanRates[5].addEventListener("click", this.onScanRateClick.custom);

        setInterval(Index.getBeamControlOutput, 1000)
    },

    /**
     * Disable user elements to prevent user from pressing buttons when system is not powered
     * @param {bool} state
     */
    disableMainElements: function(state) {
        this.components.btnElectronBeamAlign.disabled = state;
        this.components.btnStartScan.disabled = state;
        this.components.btnSaveScan.disabled = state;
        this.components.sliderImageBrightness.disabled = state;
        this.components.sliderImageContrast.disabled = state;
        this.components.sliderImageMagnify.disabled = state;

        for (var i=0; i < this.components.radioScanRates.length; i++) {
            this.components.radioScanRates[i].disabled = state;
        }

        // For sliders, add/remove the disabled css class to prevent user from moving sliders
        if (state) {
            this.components.sliderImageBrightness.classList.add("slider-disabled")
            this.components.sliderImageMagnify.classList.add("slider-disabled")
            this.components.sliderImageContrast.classList.add("slider-disabled")
        }
        else {
            this.components.sliderImageBrightness.classList.remove("slider-disabled")
            this.components.sliderImageMagnify.classList.remove("slider-disabled")
            this.components.sliderImageContrast.classList.remove("slider-disabled")
        }
    },

    disableScanElements: function(state) {
        Index.components.btnStartScan.disabled = state;
        Index.components.btnStopScan.disabled = !state;

        // User shouldn't be able to power system off during scan
        Index.components.btnElectronBeamOn.disabled = state;
        Index.components.btnElectronBeamAlign.disabled = state;

        for (var i=0; i < this.components.radioScanRates.length; i++) {
            Index.components.radioScanRates[i].disabled = state;
        }
    },

    onElectronBeamOnClick: function() {
        var btnText, route;

        // Toggle button text/style from on to off
        if(Index.components.btnElectronBeamOn.innerText == "Power On") {
            btnText = "Power Off";
            route = Index.routes.postElectronBeamOn;
            Index.disableMainElements(false);
        }
        else {
            btnText = "Power On";
            route = Index.routes.postElectronBeamOff;
            Index.disableMainElements(true);
        }

        Index.components.btnElectronBeamOn.disabled = true;

        fetchPost(route)
            .then(function() {
                Index.components.btnElectronBeamOn.innerText = btnText;

                Index.components.btnElectronBeamOn.classList.toggle("btn-dark")
                Index.components.btnElectronBeamOn.classList.toggle("btn-danger")

                Index.components.btnElectronBeamOn.disabled = false;
            })
    },

    onElectronBeamAlignClick: function() {
        var result = confirm("Are you sure you want to align the electron beam? This may take a while.")

        if (result == true) {
            Index.components.btnElectronBeamOn.disabled = true;
            Index.components.btnElectronBeamAlign.disabled = true;
            Index.components.btnStartScan.disabled = true;

            fetchPost(Index.routes.postElectronBeamAlign)
            .then(function() {
                Index.components.btnElectronBeamOn.disabled = false;
                Index.components.btnElectronBeamAlign.disabled = false;
                Index.components.btnStartScan.disabled = false;

                alert("Beam alignment complete.")
            })
        }
        else {
            console.log("Electron beam alignment cancelled.")
        }
    },

    onStartScanClick: function() {
        console.log("Start")
        $.post(Index.routes.postStartStream)
        Index.disableScanElements(true);
    },

    onStopScanClick: function() {
        console.log("Stop")
        $.post(Index.routes.postStopStream)
        Index.disableScanElements(false);
    },

    onImageMagnifyChange: function() {
        let data = {
            value: parseFloat(Index.components.sliderImageMagnify.value)
        }
        fetchPost(Index.routes.postImageMagnify, data)
    },

    onImageBrightnessChange: function() {
        let data = {
            value: parseFloat(Index.components.sliderImageBrightness.value)
        }
        fetchPost(Index.routes.postImageBrightness, data)
    },

    onImageContrastChange: function() {
        let data = {
            value: parseFloat(Index.components.sliderImageContrast.value)
        }
        fetchPost(Index.routes.postImageContrast, data)
    },

    setScanRate: function(data) {
        Index.components.btnStartScan.disabled = true;

        fetchPost(Index.routes.postScanRate, data)
        .then(function() {
            Index.components.btnStartScan.disabled = false;
        })
    },

    onScanRateClick: {
        slowest: function() {
            Index.setScanRate({key: "Slowest"})
        },
        slow: function() {
            Index.setScanRate({key: "Slow"})
        },
        normal: function() {
            Index.setScanRate({key: "Normal"})
        },
        fast: function() {
            Index.setScanRate({key: "Fast"})
        },
        fastest: function() {
            Index.setScanRate({key: "Fastest"})
        },
        custom: function() {
            Index.setScanRate({key: "Custom"})
        },
    },

    getBeamControlOutput: function() {
        // Only update values if user is in the current tab
        if ( document.hasFocus() ) {
            fetchGet(Index.routes.getBeamControlOutput)
            .then(function(response) {
                Index.components.displayAccelerationVoltage.innerText = response["voltage"] + " kV";
            });
        }
    },
}

window.addEventListener("load", function() {
    this.console.log("Loaded index.js")
    Index.init();
})
