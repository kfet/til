## Report Go test coverage for all packages

Write coverage to file `cover.out` and then print a report based on it
```
go test ./... -coverprofile cover.out
go tool cover -func cover.out
```

Same as above but a one-liner using a tmp file, which is `rm`-ed at the end
```
OUT=$(mktemp); go test ./... -coverprofile="$OUT" && go tool cover -func="$OUT"; rm "$OUT"
```
