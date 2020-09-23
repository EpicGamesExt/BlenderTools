ARG IMAGE

FROM $IMAGE

USER root

RUN chmod -R a+rwx /home/ue4/BlenderTools/

WORKDIR /home/ue4/

COPY . ./BlenderTools/

USER ue4

WORKDIR /home/ue4/BlenderTools/test/scripts/

CMD ["python3", "run_unit_tests.py", "--ci"]