ARG IMAGE

FROM $IMAGE

USER root

WORKDIR /home/

COPY . ./BlenderTools/

RUN chmod -R a+rwx /home/BlenderTools/

USER ue4

WORKDIR /home/BlenderTools/test/scripts/

CMD ["python3", "run_unit_tests.py", "--ci"]