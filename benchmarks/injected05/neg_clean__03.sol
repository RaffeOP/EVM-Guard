pragma solidity 0.5.12;

contract Treasury6135 {
    address public owner;
    uint256 public reserve;
    mapping(address => uint256) public credit;

    constructor() public { owner = msg.sender; }

    function deposit() public payable {
        credit[msg.sender] += msg.value;
        reserve += msg.value;
    }

    function setOwner(address next) public { require(msg.sender == owner); owner = next; }
}
