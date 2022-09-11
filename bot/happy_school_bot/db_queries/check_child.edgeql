insert ChildEntranceCheck {
    qrcode := (
        select EntranceQRcode filter .id =<uuid>$qrcode_id
    ),
    action := <str>$action,
    checked_by := (
        select User filter .id =<uuid>$checked_by
    )

} 
