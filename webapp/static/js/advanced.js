var Advanced = {
    components: {
        inputBeamControlAccelVoltage: document.getElementById("inputBeamControlAccelVoltage"),
        inputBeamControlEmissionCurrent: document.getElementById("inputBeamControlEmissionCurrent"),
        inputVoltageControlSignal: document.getElementById("inputVoltageControlSignal"),
        inputStageFastAxisScanRate: document.getElementById("inputStageFastAxisScanRate"),
        inputStageSlowAxisScanRate: document.getElementById("inputStageSlowAxisScanRate"),
        inputStageCustomFastAxisScanRate: document.getElementById("inputStageCustomFastAxisScanRate"),
        inputStageCustomSlowAxisScanRate: document.getElementById("inputStageCustomSlowAxisScanRate"),
        inputBeamFastAxisScanRate: document.getElementById("inputBeamFastAxisScanRate"),
        inputBeamSlowAxisScanRate: document.getElementById("inputBeamSlowAxisScanRate"),
        inputDetectorBias: document.getElementById("inputDetectorBias"),
        selectBrightnessMap: document.getElementById("selectBrightnessMap"),
        inputResolution: document.getElementById("inputResolution"),
    },

    routes: {
        getBeamControlOutput: "/api/get_beam_control_output",
        setInputVoltageControlSignal: "/api/set_input_voltage_control_signal",
        setStageFastAxisScanRate: "/api/set_stage_fast_axis_scan_rate",
        setStageSlowAxisScanRate: "/api/set_stage_slow_axis_scan_rate",
        setStageCustomFastAxisScanRate: "/api/set_stage_custom_fast_axis_scan_rate",
        setStageCustomSlowAxisScanRate: "/api/set_stage_custom_slow_axis_scan_rate",
        setBeamFastAxisScanRate: "/api/set_beam_fast_axis_scan_rate",
        setBeamSlowAxisScanRate: "/api/set_beam_slow_axis_scan_rate",
        setDetectorBias: "/api/set_detector_bias",
        setBrightnessMap: "/api/set_brightness_map",
        setResolution: "/api/set_resolution",
    },

    init: function() {
        this.bindUI();
    },

    bindUI: function() {
        this.components.inputVoltageControlSignal.addEventListener("change", this.onVoltageControlSignalChange);
        // TODO(justin): Confirm if this is safe to delete
        // this.components.inputStageFastAxisScanRate.addEventListener("change", this.onStageFastAxisScanRateChange);
        // this.components.inputStageSlowAxisScanRate.addEventListener("change", this.onStageSlowAxisScanRateChange);
        this.components.inputStageCustomFastAxisScanRate.addEventListener("change", this.setStageCustomFastAxisScanRate);
        // this.components.inputStageCustomSlowAxisScanRate.addEventListener("change", this.setStageCustomSlowAxisScanRate);
        this.components.inputBeamFastAxisScanRate.addEventListener("change", this.onBeamFastAxisScanRateChange);
        this.components.inputBeamSlowAxisScanRate.addEventListener("change", this.onBeamSlowAxisScanRateChange);
        this.components.inputDetectorBias.addEventListener("change", this.onDetectorBiasChange);
        this.components.selectBrightnessMap.addEventListener("change", this.onBrightnessMapChange);
        this.components.inputResolution.addEventListener("change", this.setResolution);

        // Display live values for beam control voltage and current output
        setInterval(Advanced.getBeamControlOutput, 1000)
    },

    getBeamControlOutput: function() {
        // Only update values if user is in the current tab
        if ( document.hasFocus() ) {
            fetchGet(Advanced.routes.getBeamControlOutput)
            .then(function(response) {
                Advanced.components.inputBeamControlAccelVoltage.value = response["voltage"];
                Advanced.components.inputBeamControlEmissionCurrent.value = response["current"];
            });
        }
    },

    onVoltageControlSignalChange: function() {
        fetchPost(
            Advanced.routes.setInputVoltageControlSignal,
            { value: parseFloat(Advanced.components.inputVoltageControlSignal.value) }
        )
    },

    onStageFastAxisScanRateChange: function() {
        fetchPost(
            Advanced.routes.setStageFastAxisScanRate,
            { value: parseFloat(Advanced.components.inputStageFastAxisScanRate.value) }
        )
    },

    onStageSlowAxisScanRateChange: function() {
        fetchPost(
            Advanced.routes.setStageSlowAxisScanRate,
            { value: parseFloat(Advanced.components.inputStageSlowAxisScanRate.value) }
        )
    },

    setStageCustomFastAxisScanRate: function() {
        fetchPost(
            Advanced.routes.setStageCustomFastAxisScanRate,
            { value: parseFloat(Advanced.components.inputStageCustomFastAxisScanRate.value)}
        )
    },

    setResolution: function() {
        fetchPost(
            Advanced.routes.setResolution,
            { value: parseFloat(Advanced.components.inputResolution.value)}
        )
    },

    // setStageCustomSlowAxisScanRate: function() {
    //     fetchPost(
    //         Advanced.routes.setStageCustomSlowAxisScanRate,
    //         { value: parseFloat(Advanced.components.inputStageCustomSlowAxisScanRate.value)}
    //     )
    // },

    onBeamFastAxisScanRateChange: function() {
        fetchPost(
            Advanced.routes.setBeamFastAxisScanRate,
            { value: parseFloat(Advanced.components.inputBeamFastAxisScanRate.value) }
        )
    },

    onBeamSlowAxisScanRateChange: function() {
        fetchPost(
            Advanced.routes.setBeamSlowAxisScanRate,
            { value: parseFloat(Advanced.components.inputBeamSlowAxisScanRate.value) }
        )
    },

    onDetectorBiasChange: function() {
        fetchPost(
            Advanced.routes.setDetectorBias,
            { value: parseFloat(Advanced.components.inputDetectorBias.value) }
        )
    },

    onBrightnessMapChange: function() {
        let value = Advanced.components.selectBrightnessMap.value;

        // Cast values to boolean
        if (value == "true") {
            value = true;
        }
        else {
            value = false;
        }

        fetchPost(
            Advanced.routes.setBrightnessMap,
            { value: value }
        )
    },
}

window.addEventListener("load", function() {
    this.console.log("Loaded advanced.js")
    Advanced.init();
})
