/**
 * Convenience wrapper around the fetch  [pstrequest. Returns the response in json format and
 * reroutes to internal server error page on error.
 *
 * @param {string} url
 * @param {*} data
 */
function fetchPost(url, data) {
    return fetch(url, {
            headers: {
                'Content-Type': 'application/json'
            },
            method: "POST",
            cache: "no-cache",
            body: JSON.stringify(data)
        })
        .then(function(response) {
            // Convert response to json before using
            return response.json();
        })
        .catch(function(error) {
            // Redirect to internal server error page on error.
            // Could also show an alert instead
            window.location.href = "internal_server_error"
        })
}

/**
 * Convenience wrapper around the fetch get request. Returns the response in json format and
 * reroutes to internal server error page on error.
 *
 * @param {string} url
 */
function fetchGet(url) {
    return fetch(url, {
            headers: {
                'Content-Type': 'application/json'
            },
            method: "GET",
            cache: "no-cache",
        })
        .then(function(response) {
            // Convert response to json before using
            return response.json();
        })
        .catch(function(error) {
            // Redirect to internal server error page on error.
            // Could also show an alert instead
            window.location.href = "internal_server_error"
        })
}
