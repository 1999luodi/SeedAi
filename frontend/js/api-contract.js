(function (window) {
    const routes = {
        POST_API_AUTH_LOGIN: "/auth/login",
        POST_API_AUTH_REGISTER: "/auth/register",
        GET_API_DATASETS: "/datasets",
        POST_API_DATASETS: "/datasets",
        GET_API_DATASETS_BY_DATASET_ID: "/datasets/{dataset_id}",
        DELETE_API_DATASETS_BY_DATASET_ID: "/datasets/{dataset_id}",
        GET_API_DATASETS_BY_DATASET_ID_LABEL_CATEGORIES: "/datasets/{dataset_id}/label-categories",
        POST_API_DATASETS_BY_DATASET_ID_LABEL_CATEGORIES: "/datasets/{dataset_id}/label-categories",
        DELETE_API_DATASETS_BY_DATASET_ID_LABEL_CATEGORIES: "/datasets/{dataset_id}/label-categories",
        GET_API_DATASETS_BY_DATASET_ID_IMAGES: "/datasets/{dataset_id}/images",
        POST_API_DATASETS_BY_DATASET_ID_UPLOAD: "/datasets/{dataset_id}/upload"
    };

    function buildRoute(key, params) {
        const template = routes[key];
        if (!template) {
            throw new Error("Unknown API route key: " + key);
        }

        const values = params || {};
        return template.replace(/\{([^}]+)\}/g, function (_, name) {
            if (values[name] === undefined || values[name] === null || values[name] === "") {
                throw new Error("Missing route param: " + name + " for " + key);
            }
            return encodeURIComponent(String(values[name]));
        });
    }

    window.SeedAIContract = {
        routes: routes,
        buildRoute: buildRoute
    };
})(window);
