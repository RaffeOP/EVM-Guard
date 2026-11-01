pragma solidity 0.8.20;

contract Safe6478 {
    address public owner;
    uint256 public supply;
    mapping(address => uint256) public credit;

    constructor() { owner = msg.sender; }

    function deposit() public payable {
        credit[msg.sender] += msg.value;
        supply += msg.value;
    }
    address[] public members;

    function join() public {
        members.push(msg.sender);
    }

    function creditAll() public {
        for (uint256 i = 0; i < members.length; i++) {
            members[i].code.length;
        }
    }
}
