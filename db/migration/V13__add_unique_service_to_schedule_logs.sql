DELETE FROM public.schedule_logs a
USING public.schedule_logs b
WHERE a.sn > b.sn
  AND a.service = b.service;

ALTER TABLE public.schedule_logs
  ADD CONSTRAINT schedule_logs_service_uniq UNIQUE (service);
