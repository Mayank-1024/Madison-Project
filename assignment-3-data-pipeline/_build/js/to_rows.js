// Turn the clean bundle into one item per record, so each record becomes one CSV row.
return $input.first().json.records.map((json) => ({ json }));
